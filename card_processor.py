"""
وظائف خاصة لمعالجة البطاقات المرسلة من المستخدم
Card processing functions for user-submitted cards
"""

import re
import random
from luhn import calculate_luhn_checksum


def parse_card_format(card_text):
    """
    تحليل البطاقة المرسلة بصيغة: 5154620012228852|05|2029|704
    
    Args:
        card_text: النص المرسل من المستخدم
    
    Returns:
        قاموس يحتوي على معلومات البطاقة أو None إذا كانت الصيغة خاطئة
    """
    # تنظيف النص
    card_text = card_text.strip()
    
    # النمط المتوقع: 16 رقم|شهر|سنة|cvv
    # مثال: 5154620012228852|05|2029|704
    pattern = r'^(\d{16})\|(\d{2})\|(\d{4})\|(\d{3,4})$'
    
    match = re.match(pattern, card_text)
    
    if not match:
        return None
    
    card_number = match.group(1)
    month = match.group(2)
    year = match.group(3)
    cvv = match.group(4)
    
    return {
        'card_number': card_number,
        'month': month,
        'year': year,
        'cvv': cvv,
        'full_bin': card_number[:12]  # أول 12 رقم
    }


def regenerate_card(card_info):
    """
    إعادة توليد آخر 4 أرقام من البطاقة + CVV جديد
    يبقى التاريخ كما هو
    
    Args:
        card_info: معلومات البطاقة من parse_card_format
    
    Returns:
        قاموس يحتوي على البطاقة الجديدة
    """
    # أخذ أول 12 رقم
    bin_12 = card_info['full_bin']
    
    # توليد 3 أرقام عشوائية (رقم 13، 14، 15)
    random_3_digits = ''.join([str(random.randint(0, 9)) for _ in range(3)])
    
    # تجميع أول 15 رقم
    partial_card = bin_12 + random_3_digits
    
    # حساب رقم التحقق Luhn (الرقم 16)
    checksum = calculate_luhn_checksum(partial_card)
    
    # البطاقة الكاملة الجديدة
    new_card_number = partial_card + str(checksum)
    
    # توليد CVV جديد (نفس الطول)
    cvv_length = len(card_info['cvv'])
    if cvv_length == 4:
        new_cvv = str(random.randint(1000, 9999))
    else:
        new_cvv = str(random.randint(100, 999))
    
    return {
        'card_number': new_card_number,
        'month': card_info['month'],
        'year': card_info['year'],
        'cvv': new_cvv
    }


def format_card_output(card_info):
    """
    تنسيق البطاقة بنفس صيغة الإدخال
    
    Args:
        card_info: معلومات البطاقة
    
    Returns:
        نص منسق: 5154620012221234|05|2029|892
    """
    return f"{card_info['card_number']}|{card_info['month']}|{card_info['year']}|{card_info['cvv']}"


def detect_card_type(card_number):
    """
    الكشف عن نوع البطاقة من أول رقمين
    
    Args:
        card_number: رقم البطاقة
    
    Returns:
        نوع البطاقة كنص
    """
    first_digit = card_number[0]
    first_two = card_number[:2]
    
    if first_digit == '4':
        return 'Visa'
    elif first_two in ['51', '52', '53', '54', '55'] or (22 <= int(first_two) <= 27):
        return 'Mastercard'
    elif first_two in ['34', '37']:
        return 'American Express'
    elif first_two in ['60', '65'] or first_two == '64':
        return 'Discover'
    else:
        return 'Unknown'


if __name__ == "__main__":
    # اختبار
    print("🧪 Testing Card Regeneration...\n")
    
    test_input = "5154620012228852|05|2029|704"
    print(f"📥 Input: {test_input}")
    
    card_info = parse_card_format(test_input)
    if card_info:
        print(f"✅ Parsed successfully!")
        print(f"   BIN (first 12): {card_info['full_bin']}")
        print(f"   Date: {card_info['month']}/{card_info['year']}")
        
        new_card = regenerate_card(card_info)
        output = format_card_output(new_card)
        
        print(f"\n📤 Output: {output}")
        print(f"   Type: {detect_card_type(new_card['card_number'])}")
        print(f"   Last 4 digits changed: {card_info['card_number'][-4:]} → {new_card['card_number'][-4:]}")
        print(f"   CVV changed: {card_info['cvv']} → {new_card['cvv']}")
        print(f"   Date kept: {card_info['month']}/{card_info['year']}")
