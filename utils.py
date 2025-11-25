"""
وظائف مساعدة للبوت
Utility functions for the bot
"""

import random
from datetime import datetime, timedelta


def generate_expiry_date():
    """
    توليد تاريخ انتهاء عشوائي في المستقبل
    
    Returns:
        تاريخ الانتهاء بصيغة MM/YY
    """
    current_date = datetime.now()
    
    # تاريخ انتهاء بين 1-5 سنوات من الآن
    years_to_add = random.randint(1, 5)
    months_to_add = random.randint(0, 11)
    
    expiry_date = current_date + timedelta(days=365 * years_to_add + 30 * months_to_add)
    
    return expiry_date.strftime("%m/%y")


def generate_cvv(card_type='visa'):
    """
    توليد CVV عشوائي
    
    Args:
        card_type: نوع البطاقة (amex يستخدم 4 أرقام، الباقي 3 أرقام)
    
    Returns:
        CVV كنص
    """
    if card_type.lower() == 'amex':
        return str(random.randint(1000, 9999))  # 4 digits
    else:
        return str(random.randint(100, 999))    # 3 digits


def get_card_info(card_type):
    """
    الحصول على معلومات عن نوع البطاقة
    
    Args:
        card_type: نوع البطاقة
    
    Returns:
        قاموس يحتوي على معلومات البطاقة
    """
    card_info = {
        'visa': {
            'name': 'Visa',
            'emoji': '💳',
            'length': 16,
            'cvv_length': 3
        },
        'mastercard': {
            'name': 'Mastercard',
            'emoji': '💳',
            'length': 16,
            'cvv_length': 3
        },
        'amex': {
            'name': 'American Express',
            'emoji': '💎',
            'length': 15,
            'cvv_length': 4
        },
        'discover': {
            'name': 'Discover',
            'emoji': '🔍',
            'length': 16,
            'cvv_length': 3
        }
    }
    
    return card_info.get(card_type.lower(), card_info['visa'])


def format_card_details(card_number, card_type, include_extra=True):
    """
    تنسيق تفاصيل البطاقة للعرض
    
    Args:
        card_number: رقم البطاقة
        card_type: نوع البطاقة
        include_extra: هل نضيف CVV وتاريخ الانتهاء
    
    Returns:
        نص منسق لعرض البطاقة
    """
    from luhn import format_card_number
    
    info = get_card_info(card_type)
    formatted_number = format_card_number(card_number)
    
    result = f"{info['emoji']} **{info['name']}**\n"
    result += f"```\n{formatted_number}\n```"
    
    if include_extra:
        expiry = generate_expiry_date()
        cvv = generate_cvv(card_type)
        result += f"\n📅 Expiry: `{expiry}`\n"
        result += f"🔒 CVV: `{cvv}`"
    
    return result


def get_card_type_keyboard():
    """
    إنشاء لوحة مفاتيح inline لاختيار نوع البطاقة
    
    Returns:
        قائمة بصفوف الأزرار
    """
    from telegram import InlineKeyboardButton
    
    keyboard = [
        [
            InlineKeyboardButton("💳 Visa", callback_data='gen_visa'),
            InlineKeyboardButton("💳 Mastercard", callback_data='gen_mastercard')
        ],
        [
            InlineKeyboardButton("💎 Amex", callback_data='gen_amex'),
            InlineKeyboardButton("🔍 Discover", callback_data='gen_discover')
        ],
        [
            InlineKeyboardButton("🎲 Random", callback_data='gen_random')
        ]
    ]
    
    return keyboard


def get_quantity_keyboard():
    """
    إنشاء لوحة مفاتيح inline لاختيار الكمية
    
    Returns:
        قائمة بصفوف الأزرار
    """
    from telegram import InlineKeyboardButton
    
    keyboard = [
        [
            InlineKeyboardButton("1️⃣ One", callback_data='qty_1'),
            InlineKeyboardButton("5️⃣ Five", callback_data='qty_5'),
            InlineKeyboardButton("🔟 Ten", callback_data='qty_10')
        ]
    ]
    
    return keyboard


if __name__ == "__main__":
    # اختبار الوظائف
    print("🧪 Testing Utility Functions...\n")
    
    print(f"📅 Random Expiry Date: {generate_expiry_date()}")
    print(f"🔒 Visa CVV: {generate_cvv('visa')}")
    print(f"🔒 Amex CVV: {generate_cvv('amex')}\n")
    
    # اختبار تنسيق البطاقة
    test_card = "4532015112830366"
    print(format_card_details(test_card, 'visa'))
