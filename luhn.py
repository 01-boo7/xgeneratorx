"""
خوارزمية Luhn لتوليد والتحقق من أرقام البطاقات الائتمانية التجريبية
Luhn Algorithm for generating and validating test credit card numbers
"""

import random


# BIN numbers (Bank Identification Numbers) لأنواع البطاقات المختلفة
# استخدام BINs معروفة ومقبولة على نطاق واسع للاختبار
CARD_BINS = {
    # Visa - BINs شائعة ومقبولة
    'visa': [
        '4532',  # Visa (very common test BIN)
        '4539',  # Visa 
        '4556',  # Visa 
        '4916',  # Visa 
        '4929',  # Visa
        '4485',  # Visa
        '4024',  # Visa
    ],
    # Mastercard - BINs شائعة ومقبولة
    'mastercard': [
        '5425',  # Mastercard (very common)
        '5555',  # Mastercard (very common)
        '5105',  # Mastercard
        '5454',  # Mastercard
        '2221',  # Mastercard (new range)
        '2720',  # Mastercard (new range)
    ],
    # American Express - 15 digits
    'amex': [
        '3782',  # Amex
        '3714',  # Amex
        '3787',  # Amex
        '3747',  # Amex
    ],
    # Discover
    'discover': [
        '6011',  # Discover
        '6221',  # Discover (China UnionPay)
        '6529',  # Discover
        '6444',  # Discover
    ],
}


def calculate_luhn_checksum(card_number):
    """
    حساب رقم التحقق Luhn checksum لرقم البطاقة

    Args:
        card_number: رقم البطاقة بدون رقم التحقق (string)

    Returns:
        رقم التحقق (int)
    """
    def digits_of(n):
        return [int(d) for d in str(n)]

    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]

    checksum = 0
    for d in odd_digits:
        checksum += sum(digits_of(d * 2))
    checksum += sum(even_digits)

    return (10 - (checksum % 10)) % 10


def validate_luhn(card_number):
    """
    التحقق من صحة رقم البطاقة باستخدام خوارزمية Luhn

    Args:
        card_number: رقم البطاقة الكامل (string)

    Returns:
        True إذا كان الرقم صحيح، False إذا لم يكن صحيح
    """
    try:
        card_number = card_number.replace(' ', '').replace('-', '')
        check_digit = int(card_number[-1])
        calculated = calculate_luhn_checksum(card_number[:-1])
        return check_digit == calculated
    except (ValueError, IndexError):
        return False


def generate_card_number(card_type='visa', quantity=1):
    """
    توليد رقم/أرقام بطاقة تجريبية صالحة

    Args:
        card_type: نوع البطاقة (visa, mastercard, amex, discover)
        quantity: عدد البطاقات المطلوب توليدها

    Returns:
        قائمة بأرقام البطاقات المولدة
    """
    card_type = card_type.lower()

    if card_type not in CARD_BINS:
        card_type = 'visa'  # default

    cards = []

    for _ in range(quantity):
        # اختيار BIN عشوائي من النوع المحدد
        bin_number = random.choice(CARD_BINS[card_type])

        # تحديد طول البطاقة (15 لـ Amex، 16 للباقي)
        card_length = 15 if card_type == 'amex' else 16

        # توليد باقي الأرقام عشوائياً (ما عدا آخر رقم checksum)
        remaining_length = card_length - len(bin_number) - 1
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(remaining_length)])

        # تجميع الرقم بدون checksum
        partial_card = bin_number + random_digits

        # حساب وإضافة رقم التحقق
        checksum = calculate_luhn_checksum(partial_card)
        full_card = partial_card + str(checksum)

        cards.append(full_card)

    return cards


def format_card_number(card_number):
    """
    تنسيق رقم البطاقة بمسافات للقراءة

    Args:
        card_number: رقم البطاقة (string)

    Returns:
        رقم البطاقة منسق
    """
    # Amex: XXXX XXXXXX XXXXX
    if len(card_number) == 15:
        return f"{card_number[:4]} {card_number[4:10]} {card_number[10:]}"
    # Others: XXXX XXXX XXXX XXXX
    else:
        return ' '.join([card_number[i:i+4] for i in range(0, len(card_number), 4)])


if __name__ == "__main__":
    # اختبار الخوارزمية
    print("🧪 Testing Luhn Algorithm...\n")

    # اختبار التوليد
    for card_type in CARD_BINS.keys():
        cards = generate_card_number(card_type, 2)
        print(f"✅ {card_type.upper()}:")
        for card in cards:
            formatted = format_card_number(card)
            is_valid = validate_luhn(card)
            print(f"   {formatted} - Valid: {is_valid}")
        print()
