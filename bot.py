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

# إعداد logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.effective_user
    welcome_message = f"""
🎉 **مرحباً {user.first_name}!**

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
    await query.answer()
    
    callback_data = query.data
    
    # معالجة اختيار نوع البطاقة
    if callback_data.startswith('gen_'):
        card_type = callback_data.replace('gen_', '')
        
        # حفظ نوع البطاقة في context
        context.user_data['card_type'] = card_type
        
        # عرض خيارات الكمية
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
        card_type = context.user_data.get('card_type', 'visa')
        
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
        
        logger.info(f"Generated {quantity} {card_type} cards for user {query.from_user.id}")


async def handle_card_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية - لمعالجة البطاقات المرسلة"""
    user_message = update.message.text.strip()
    
    # محاولة تحليل البطاقة
    card_info = parse_card_format(user_message)
    
    if card_info:
        # البطاقة بالصيغة الصحيحة
        await update.message.reply_text("⏳ جاري المعالجة...")
        
        # توليد بطاقة جديدة
        new_card = regenerate_card(card_info)
        card_type = detect_card_type(new_card['card_number'])
        
        # تنسيق الناتج
        output = format_card_output(new_card)
        
        response = f"""✨ **تم توليد البطاقة بنجاح!**

📥 **الإدخال:**
`{user_message}`

📤 **الناتج:**
`{output}`

📊 **التفاصيل:**
• النوع: {card_type}
• آخر 4 أرقام: `{card_info['card_number'][-4:]}` → `{new_card['card_number'][-4:]}`
• CVV: `{card_info['cvv']}` → `{new_card['cvv']}`
• التاريخ: `{card_info['month']}/{card_info['year']}` (بدون تغيير)

⚠️ للاختبار فقط - ليست بطاقات حقيقية

💡 أرسل بطاقة أخرى أو استخدم /generate
"""
        
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Processed card regeneration for user {update.effective_user.id}")
    else:
        # الرسالة ليست بطاقة أو بصيغة خاطئة - نتجاهلها
        pass


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ حدث خطأ! حاول مرة أخرى.\nUse /start to restart."
            )
    except Exception as e:
        logger.error(f"Error in error_handler: {e}")


def main():
    """البدء الرئيسي للبوت"""
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
