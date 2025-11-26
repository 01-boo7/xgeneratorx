"""
بوت تيليجرام لتوليد بطاقات ائتمانية تجريبية
Telegram Bot for Generating Test Credit Cards
"""

import os
import random
import logging
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

from luhn import generate_card_number
from utils import (
    format_card_details,
    get_card_type_keyboard,
    get_quantity_keyboard,
)
from card_processor import (
    parse_card_format,
    regenerate_card,
    format_card_output,
    detect_card_type,
)
from bin_database import BINDatabase
from keep_alive import keep_alive

# إعداد logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء قاعدة بيانات BIN
bin_db = BINDatabase()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    if not update.message:
        return
    
    user = update.effective_user
    user_name = user.first_name if user else "User"
    welcome_message = f"""
🎉 **مرحباً {user_name}!**

أنا بوت توليد بطاقات ائتمانية **تجريبية** باستخدام خوارزمية Luhn ✨

⚠️ **ملاحظة مهمة:**
هذه البطاقات للاختبار فقط ولا يمكن استخدامها لعمليات شراء حقيقية.

📌 **الأوامر المتاحة:**
/generate - توليد بطاقات تجريبية
/help - المساعدة والمعلومات

💡 **أو أرسل بطاقة بهذا الشكل:**
`5154620012228852|05|2029|704`
سأولد آخر 4 أرقام جديدة + CVV جديد!

استخدم /generate للبدء! 🚀
"""
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /help"""
    if not update.message:
        return
    
    help_message = """
📖 **دليل الاستخدام**

**الأوامر الأساسية:**
/start - بدء البوت
/generate - توليد بطاقات تجريبية
/help - عرض هذه الرسالة

**معالجة البطاقات:**
أرسل بطاقة بالصيغة:
`5154620012228852|05|2029|704`

سأولد:
• آخر 4 أرقام جديدة (مع Luhn checksum)
• CVV جديد
• التاريخ يبقى كما هو

**أنواع البطاقات المدعومة:**
💳 Visa
💳 Mastercard
💎 American Express
🔍 Discover

**عن خوارزمية Luhn:**
خوارزمية Luhn (Mod 10) هي خوارزمية checksum تُستخدم للتحقق من صحة أرقام البطاقات الائتمانية.

⚠️ **تنبيه قانوني:**
• البطاقات المولدة هي أرقام تجريبية فقط
• لا يمكن استخدامها لعمليات شراء حقيقية
• الاستخدام على مسؤوليتك الخاصة
• البوت للأغراض التعليمية فقط

🤖 Built with ❤️ using Python
"""
    await update.message.reply_text(
        help_message,
        parse_mode=ParseMode.MARKDOWN
    )


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /generate - عرض خيارات نوع البطاقة"""
    if not update.message:
        return
    
    keyboard = get_card_type_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = """
🎯 **اختر نوع البطاقة:**

اختر نوع البطاقة التي تريد توليدها من الخيارات أدناه 👇
"""

    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار التفاعلية"""
    query = update.callback_query
    if not query or not query.data:
        return
    
    await query.answer()

    callback_data = query.data

    # معالجة اختيار نوع البطاقة
    if callback_data.startswith('gen_'):
        card_type = callback_data.replace('gen_', '')

        # حفظ نوع البطاقة في context
        if context and context.user_data is not None:
            context.user_data['card_type'] = card_type
        elif context:
            context.user_data = {'card_type': card_type}

        # عرض خيارات الكمية
        from telegram import InlineKeyboardMarkup
        keyboard = get_quantity_keyboard()
        reply_markup = InlineKeyboardMarkup(keyboard)

        card_name = card_type.upper() if card_type != 'random' else 'Random'
        message = f"""
✅ تم اختيار: **{card_name}**

🔢 **اختر عدد البطاقات:**
"""

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )


    # معالجة اختيار الكمية وتوليد البطاقات
    elif callback_data.startswith('qty_'):
        quantity = int(callback_data.replace('qty_', ''))
        card_type = context.user_data.get('card_type', 'visa') if context and context.user_data else 'visa'

        # إذا كان النوع random، اختر نوع عشوائي
        if card_type == 'random':
            card_type = random.choice(['visa', 'mastercard', 'amex', 'discover'])

        # توليد البطاقات
        await query.edit_message_text("⏳ جاري التوليد...")

        cards = generate_card_number(card_type, quantity)

        # تنسيق الرسالة
        response = f"✨ **تم توليد {quantity} بطاقة تجريبية**\n\n"

        for idx, card in enumerate(cards, 1):
            response += f"**البطاقة #{idx}**\n"
            response += format_card_details(card, card_type) + "\n\n"

        response += "⚠️ للاختبار فقط - ليست بطاقات حقيقية\n"
        response += "\n💡 استخدم /generate لتوليد المزيد!"

        # إرسال النتيجة
        await query.edit_message_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )

        user_id = query.from_user.id if query.from_user else "unknown"
        logger.info(f"Generated {quantity} {card_type} cards for user {user_id}")

    # معالجة زر Re-Gen
    elif callback_data.startswith('regen_'):
        # استخراج حالة BIN والبطاقة الأصلية
        parts = callback_data.replace('regen_', '').split('_', 1)
        if len(parts) == 2:
            bin_status = parts[0]  # "new" or "existing"
            original_card = parts[1]
        else:
            # للتوافق مع الأزرار القديمة
            bin_status = "existing"
            original_card = callback_data.replace('regen_', '')

        await query.answer("🔄 جاري إعادة التوليد...")
        await query.edit_message_text("⏳ جاري التوليد...")

        # تحليل البطاقة الأصلية
        card_info = parse_card_format(original_card)

        if card_info:
            card_type = detect_card_type(card_info['card_number'])

            # توليد 10 بطاقات جديدة
            cards_list = []
            for _ in range(10):
                new_card = regenerate_card(card_info)
                output = format_card_output(new_card)
                cards_list.append(output)

            # معلومات البطاقة
            bin_number = card_info['card_number'][:6]

            # تنسيق الرسالة (باستخدام الحالة الأصلية)
            response = ""

            # عرض الرسالة الأصلية (حسب حالة BIN عند أول إرسال)
            if bin_status == "new":
                response += "✅ **BIN جديد** - لم يتم استخدامه من قبل\n\n"
            else:
                # إذا كان موجود، نجلب المعلومات الحالية
                _, bin_info = bin_db.check_bin(card_info['card_number'], card_type)
                if bin_info:
                    response += bin_db.get_warning_message(bin_info) + "\n"
                else:
                    response += "✅ **BIN جديد** - لم يتم استخدامه من قبل\n\n"

            response += f"**🎴 Generator Card**\n\n"
            response += f"**Bin #:** `{original_card}`\n"
            response += "```\n"
            for card in cards_list:
                response += f"{card}\n"
            response += "```\n\n"

            # معلومات إضافية
            response += f"**ℹ️ Info:**\n"
            response += f"• Type: {card_type}\n"
            response += f"• BIN: {bin_number}\n"
            response += f"• Format: CREDIT CARD\n\n"

            # معلومات المولد
            user_name = query.from_user.first_name if query.from_user else "User"
            import datetime
            time_now = datetime.datetime.now().strftime("%I:%M %p")
            response += f"**Gen by:** {user_name} → {time_now}\n"

            # زر Re-Gen (مع الحفاظ على نفس الحالة)
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [[InlineKeyboardButton("🔄 Re-Gen", callback_data=f'regen_{bin_status}_{original_card}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # إرسال النتيجة
            await query.edit_message_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

            user_id = query.from_user.id if query.from_user else "unknown"
            logger.info(f"Re-generated 10 cards for user {user_id}")



async def handle_card_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية - لمعالجة البطاقات المرسلة"""
    if not update.message or not update.message.text:
        return
    
    user_message = update.message.text.strip()

    # محاولة تحليل البطاقة
    card_info = parse_card_format(user_message)

    if card_info:
        # البطاقة بالصيغة الصحيحة
        msg = await update.message.reply_text("⏳ جاري التحليل والتوليد...")

        # حفظ البطاقة الأصلية في context للـ Re-Gen
        if context and context.user_data is not None:
            context.user_data['original_card'] = user_message
        elif context:
            context.user_data = {'original_card': user_message}

        # التحقق من BIN في قاعدة البيانات
        card_type = detect_card_type(card_info['card_number'])
        bin_exists, bin_info = bin_db.check_bin(card_info['card_number'], card_type)

        # إضافة BIN إلى قاعدة البيانات (أو تحديث عدد الاستخدامات)
        bin_db.add_bin(card_info['card_number'], card_type)

        # توليد 10 بطاقات
        cards_list = []
        for _ in range(10):
            new_card = regenerate_card(card_info)
            output = format_card_output(new_card)
            cards_list.append(output)

        # معلومات البطاقة
        bin_number = card_info['card_number'][:6]

        # تنسيق الرسالة
        response = ""

        # إضافة تحذير إذا كان BIN موجود
        if bin_exists and bin_info:
            response += bin_db.get_warning_message(bin_info) + "\n"
        else:
            response += "✅ **BIN جديد** - لم يتم استخدامه من قبل\n\n"

        response += f"**🎴 Generator Card**\n\n"
        response += f"**Bin #:** `{user_message}`\n"
        response += "```\n"
        for idx, card in enumerate(cards_list, 1):
            response += f"{card}\n"
        response += "```\n\n"

        # معلومات إضافية
        response += f"**ℹ️ Info:**\n"
        response += f"• Type: {card_type}\n"
        response += f"• BIN: {bin_number}\n"
        response += f"• Format: CREDIT CARD\n\n"

        # معلومات المولد
        user_name = update.effective_user.first_name if update.effective_user else "User"
        import datetime
        time_now = datetime.datetime.now().strftime("%I:%M %p")
        response += f"**Gen by:** {user_name} → {time_now}\n"

        # زر Re-Gen (مع حفظ حالة BIN الأصلية)
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        bin_status = "new" if not bin_exists else "existing"
        keyboard = [[InlineKeyboardButton("🔄 Re-Gen", callback_data=f'regen_{bin_status}_{user_message}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # إرسال النتيجة
        await msg.edit_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

        user_id = update.effective_user.id if update.effective_user else "unknown"
        logger.info(f"Generated 10 cards for user {user_id}")
    else:
        # الرسالة ليست بطاقة أو بصيغة خاطئة - نتجاهلها
        pass


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    logger.error(f"Exception while handling an update: {context.error}")

    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ حدث خطأ! حاول مرة أخرى.\nUse /start to restart."
            )
    except Exception as e:
        logger.error(f"Error in error_handler: {e}")


def main():
    """البدء الرئيسي للبوت"""
    # تشغيل Keep-Alive server
    keep_alive()
    
    # الحصول على Token من متغيرات البيئة
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not token:
        logger.error("❌ Error: TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("\n⚠️  Please set your bot token:")
        print("   export TELEGRAM_BOT_TOKEN='your-token-here'")
        print("\n📖 Get your token from @BotFather on Telegram\n")
        return

    # إنشاء التطبيق
    application = Application.builder().token(token).build()

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate_command))

    # إضافة معالج الأزرار
    application.add_handler(CallbackQueryHandler(button_callback))

    # إضافة معالج الرسائل النصية (للبطاقات)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_card_message
    ))

    # إضافة معالج الأخطاء
    application.add_error_handler(error_handler)

    # بدء البوت
    logger.info("🤖 Bot started successfully!")
    print("\n✅ Bot is running...")
    print("Press Ctrl+C to stop\n")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
