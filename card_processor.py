"""
وظائف خاصة لمعالجة البطاقات المرسلة من المستخدم
Card processing functions for user-submitted cards
"""

import re
import random
from luhn import calculate_luhn_checksum


def parse_card_format(card_text):
    """
    تحليل ذكي وقوي للبطاقة - يدعم صيغ متعددة جداً
    Smart and powerful card parsing - supports many formats
    
    أمثلة مدعومة:
    - 5154620012228852|05|2029|704
    - 5333171205882075 09/28 139
    - 4610460230910523:02:2026:512
    - 5195095001277932 Exp Date 04/27 CVV2 106
    - 5172790117287059 0530 903
    - CC #: 4028521000035233|Exp: 0327|CCV: 264

    Args:
        card_text: النص المرسل من المستخدم

    Returns:
        قاموس يحتوي على معلومات البطاقة أو None إذا كانت الصيغة خاطئة
    """
    card_text = card_text.strip()
    
    # محاولة استخراج رقم البطاقة (15 أو 16 رقم)
    card_match = re.search(r'(\d{15,16})', card_text)
    if not card_match:
        return None
    
    card_number = card_match.group(1)
    
    # إزالة رقم البطاقة من النص للبحث عن التاريخ والـ CVV
    text_without_card = card_text.replace(card_number, '', 1)
    
    # ============ البحث عن التاريخ ============
    month = None
    year = None
    
    # أنماط متعددة للتاريخ - من الأكثر تحديداً إلى الأقل
    date_patterns = [
        # مع labels مثل Exp Date:, Expiry:, Date:, Exp:
        (r'(?:Exp(?:iry)?|Date)\s+(?:Date)?\s*:?\s*(\d{2})\s*[/|\-:;,\s]\s*(\d{2,4})', re.IGNORECASE),
        (r'(?:Exp(?:iry)?|Date)\s*:?\s*(\d{2})\s*[/|\-:;,\s]\s*(\d{2,4})', re.IGNORECASE),
        (r'(?:Exp(?:iry)?|Date)\s*:?\s*(\d{2})(\d{2,4})', re.IGNORECASE),
        
        # صيغة الـ pipes و colons |MM|YYYY| أو :MM:YYYY:
        (r'[|:]\s*(\d{2})\s*[|:]\s*(\d{2,4})\s*[|:]', 0),
        (r'[|:]\s*(\d{2})\s*[|:]\s*(\d{2,4})\s*(?:[|:]|$)', 0),
        
        # صيغة عامة مع فواصل مختلفة: MM/YY, MM-YY, MM:YY, MM,YY, MM;YY, MM YY
        (r'(\d{2})\s*[/|\-:;,\s]\s*(\d{2,4})', 0),
        
        # صيغة بدون فواصل بعد رقم: MMYY أو MMYYYY (يجب أن تكون محاطة بأشياء غير رقمية)
        (r'[^\d](\d{2})(\d{2})(?:\s|$)', 0),  # MMYY فقط (سنة 2 رقم)
        (r'^(\d{2})(\d{2})(?:\s|$)', 0),  # MMYY في البداية
    ]
    
    for pattern, flags in date_patterns:
        date_match = re.search(pattern, text_without_card, flags)
        if date_match:
            month = date_match.group(1)
            year_raw = date_match.group(2)
            
            # التحقق من أن الشهر صحيح (01-12)
            try:
                month_int = int(month)
                if month_int < 1 or month_int > 12:
                    continue
            except:
                continue
            
            # معالجة السنة
            if len(year_raw) == 2:
                year = '20' + year_raw
            else:
                year = year_raw
            break
    
    if not month or not year:
        return None
    
    # ============ البحث عن CVV ============
    cvv = None
    
    # أولاً: البحث عن صيغة الـ pipes - card|month|year|cvv (الأولوية الأعلى)
    pipes_match = re.search(r'\|(\d{2})\|(\d{2,4})\|([A-Z0-9]{3,4})(?:\|)?', card_text)
    if pipes_match and pipes_match.group(3):
        cvv = pipes_match.group(3)
    
    # ثانياً: البحث عن صيغة الـ colons - card:month:year:cvv
    if not cvv:
        colons_match = re.search(r':(\d{2}):(\d{2,4}):([A-Z0-9]{3,4})(?::)?', card_text)
        if colons_match and colons_match.group(3):
            cvv = colons_match.group(3)
    
    # ثالثاً: البحث عن CVV مع label (CVV, CCV, CVC, CVV2, etc)
    if not cvv:
        cvv_match = re.search(r'(?:CVV|CCV|CVC|CV|CVV2|CVC2)\s*:?\s*([A-Z0-9]{3,4})', text_without_card, re.IGNORECASE)
        if cvv_match:
            cvv = cvv_match.group(1)
    
    # رابعاً: البحث عن 3-4 أرقام محاطة بعلامات ترقيم
    if not cvv:
        cvv_match = re.search(r'\s([0-9]{3,4})\s|[\n,;:]([0-9]{3,4})[\s\n,;:]|[\n,;:]([0-9]{3,4})$', text_without_card)
        if cvv_match:
            cvv = cvv_match.group(1) or cvv_match.group(2) or cvv_match.group(3)
    
    # خامساً: أي 3-4 أرقام أخرى
    if not cvv:
        cvv_match = re.search(r'([0-9]{3,4})[^0-9]', text_without_card)
        if cvv_match and cvv_match.group(1) not in [month, year]:
            cvv = cvv_match.group(1)
    
    # إذا ما استخرجنا CVV أو ما يكون valid، استخدم XXX
    if not cvv or len(cvv) < 3 or not cvv.isdigit():
        cvv = 'XXX'
    
    # استخراج أول 12 رقم كـ BIN كامل (أو أول 6 إذا كانت البطاقة أقل من 12)
    full_bin = card_number[:12] if len(card_number) >= 12 else card_number[:6]
    
    return {
        'card_number': card_number,
        'full_bin': full_bin,
        'month': month,
        'year': year,
        'cvv': cvv,
        'card_type': detect_card_type(card_number)
    }


def regenerate_card(card_info):
    """
    توليد بطاقة جديدة بناءً على نفس BIN والتاريخ و CVV
    
    Args:
        card_info: معلومات البطاقة الأصلية
    
    Returns:
        قاموس ببيانات البطاقة الجديدة
    """
    bin_part = card_info['full_bin']
    card_length = len(card_info['card_number'])
    
    # توليد أرقام عشوائية بعد BIN
    remaining_digits = card_length - len(bin_part) - 1
    random_middle = ''.join(str(random.randint(0, 9)) for _ in range(remaining_digits))
    
    # إنشاء رقم البطاقة بدون Luhn checksum
    card_without_luhn = bin_part + random_middle
    
    # حساب Luhn checksum
    luhn_digit = calculate_luhn_checksum(card_without_luhn)
    new_card_number = card_without_luhn + str(luhn_digit)
    
    # توليد CVV جديد
    if card_info['cvv'].isdigit():
        new_cvv = ''.join(str(random.randint(0, 9)) for _ in range(len(card_info['cvv'])))
    else:
        new_cvv = card_info['cvv']
    
    return {
        'card_number': new_card_number,
        'month': card_info['month'],
        'year': card_info['year'],
        'cvv': new_cvv
    }


def generate_multiple_cards(card_info, count=10):
    """
    توليد عدة بطاقات جديدة
    
    Args:
        card_info: معلومات البطاقة الأصلية
        count: عدد البطاقات المراد توليدها
    
    Returns:
        قائمة ببيانات البطاقات الجديدة
    """
    new_cards = []
    for _ in range(count):
        new_card = regenerate_card(card_info)
        new_cards.append(new_card)
    
    return new_cards


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
    الكشف الذكي عن نوع البطاقة من BIN
    Smart detection of card type from BIN (Bank Identification Number)

    Args:
        card_number: رقم البطاقة

    Returns:
        نوع البطاقة كنص
    """
    if len(card_number) < 2:
        return 'Unknown'
    
    first_digit = card_number[0]
    first_two = card_number[:2]
    first_three = card_number[:3]
    first_four = card_number[:4]
    first_six = card_number[:6]
    
    # Visa: starts with 4
    if first_digit == '4':
        if first_six in ['417500', '405141', '405144', '450603', '450605', '450628']:
            return 'Visa Electron'
        return 'Visa'
    
    # American Express: 34 or 37 (15 digits)
    elif first_two in ['34', '37']:
        return 'American Express'
    
    # Discover: يجب فحصه قبل Maestro و RuPay
    # 6011, 622126-622925, 644-649, 65
    elif first_four == '6011':
        return 'Discover'
    elif first_six >= '622126' and first_six <= '622925':
        return 'Discover'
    elif first_four >= '6440' and first_four <= '6499':
        return 'Discover'
    elif first_two == '65':
        return 'Discover'
    
    # Mastercard: 51-55 or 2221-2720
    elif first_two in ['51', '52', '53', '54', '55']:
        return 'Mastercard'
    elif first_two == '22' and 21 <= int(first_four) <= 27 and 20 <= int(first_six[2:4]) <= 99:
        return 'Mastercard'
    
    # RuPay: 508, 509, 606, 607, 608 (فحص قبل China UnionPay و Maestro)
    elif first_four in ['5081', '5082', '5090', '6061', '6062', '6063', '6064', '6065', '6066', '6067', '6068']:
        return 'RuPay'
    elif first_three in ['508', '509', '606', '607', '608']:
        return 'RuPay'
    
    # China UnionPay: 62, 81
    elif first_two in ['62', '81']:
        return 'China UnionPay'
    
    # JCB: 3528-3589
    elif first_four >= '3528' and first_four <= '3589':
        return 'JCB'
    
    # Diners Club: 36, 38, 39, 300-305
    elif first_two in ['36', '38', '39']:
        return 'Diners Club'
    elif first_four >= '3000' and first_four <= '3059':
        return 'Diners Club'
    
    # Maestro: 50, 56-69 (ما لم يكن محدداً أعلاه)
    elif first_two == '50':
        return 'Maestro'
    elif first_two >= '56' and first_two <= '69':
        return 'Maestro'
    
    # Mir: 2200-2204
    elif first_four >= '2200' and first_four <= '2204':
        return 'Mir'
    
    # UATP: 1
    elif first_digit == '1':
        return 'UATP'
    
    else:
        return 'Unknown'


if __name__ == "__main__":
    print("🧪 Testing Card Regeneration...\n")

    test_input = "5195095001277932 Exp Date  04/27 CVV2  106"
    print(f"📥 Input: {test_input}")

    card_info = parse_card_format(test_input)
    if card_info:
        print(f"✅ Parsed successfully!")
        print(f"   Card Type: {card_info['card_type']}")
        print(f"   BIN (first 12): {card_info['full_bin']}")
        print(f"   Date: {card_info['month']}/{card_info['year']}")
        print(f"   CVV: {card_info['cvv']}")

        new_card = regenerate_card(card_info)
        output = format_card_output(new_card)

        print(f"\n📤 Output: {output}")
        print(f"   Type: {detect_card_type(new_card['card_number'])}")
