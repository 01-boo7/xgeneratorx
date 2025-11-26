"""
إدارة قاعدة بيانات BINs للبطاقات الائتمانية
BIN Database Manager for Credit Card BINs
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple


class BINDatabase:
    """قاعدة بيانات لحفظ وإدارة BINs المستخدمة"""
    
    def __init__(self, db_file='bin_database.json'):
        """
        تهيئة قاعدة البيانات
        
        Args:
            db_file: مسار ملف قاعدة البيانات
        """
        self.db_file = db_file
        self.data = self._load_database()
    
    def _load_database(self) -> Dict:
        """تحميل قاعدة البيانات من الملف"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_database(self):
        """حفظ قاعدة البيانات إلى الملف"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving database: {e}")
    
    def extract_bin(self, card_number: str) -> str:
        """
        استخراج أول 6 أرقام (BIN) من رقم البطاقة
        
        Args:
            card_number: رقم البطاقة
            
        Returns:
            BIN (6 أرقام)
        """
        # إزالة المسافات والرموز
        clean_card = ''.join(filter(str.isdigit, card_number))
        return clean_card[:6] if len(clean_card) >= 6 else clean_card
    
    def check_bin(self, card_number: str, card_type: str = None) -> Tuple[bool, Optional[Dict]]:
        """
        التحقق من وجود BIN في قاعدة البيانات
        
        Args:
            card_number: رقم البطاقة الكامل أو BIN
            card_type: نوع البطاقة (اختياري)
            
        Returns:
            (موجود: bool, معلومات BIN: dict أو None)
        """
        bin_number = self.extract_bin(card_number)
        
        if bin_number in self.data:
            bin_info = self.data[bin_number].copy()
            return True, bin_info
        
        return False, None
    
    def add_bin(self, card_number: str, card_type: str = None):
        """
        إضافة BIN جديد إلى قاعدة البيانات
        
        Args:
            card_number: رقم البطاقة الكامل أو BIN
            card_type: نوع البطاقة (visa, mastercard, amex, discover)
        """
        bin_number = self.extract_bin(card_number)
        
        if not card_type:
            card_type = 'Unknown'
        
        if bin_number in self.data:
            self.data[bin_number]['usage_count'] += 1
            self.data[bin_number]['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            self.data[bin_number] = {
                'card_type': str(card_type).upper() if card_type else 'Unknown',
                'first_used': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_used': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'usage_count': 1
            }
        
        self._save_database()
    
    def get_warning_message(self, bin_info: Dict) -> str:
        """
        إنشاء رسالة تحذير عند استخدام BIN موجود
        
        Args:
            bin_info: معلومات BIN من قاعدة البيانات
            
        Returns:
            رسالة التحذير
        """
        first_used = bin_info.get('first_used', 'غير معروف')
        usage_count = bin_info.get('usage_count', 0)
        card_type = bin_info.get('card_type', 'Unknown')
        
        try:
            date_obj = datetime.strptime(first_used, '%Y-%m-%d %H:%M:%S')
            formatted_date = date_obj.strftime('%d/%m/%Y')
        except:
            formatted_date = first_used
        
        warning = f"⚠️ **تحذير:** هذا الـ BIN مستخدم من قبل!\n"
        warning += f"📅 تاريخ أول استخدام: {formatted_date}\n"
        warning += f"🔢 عدد مرات الاستخدام: {usage_count}\n"
        warning += f"💳 نوع البطاقة: {card_type}\n"
        
        return warning
    
    def get_stats(self) -> Dict:
        """
        الحصول على إحصائيات قاعدة البيانات
        
        Returns:
            dict مع إحصائيات قاعدة البيانات
        """
        total_bins = len(self.data)
        
        type_counts = {}
        for bin_info in self.data.values():
            card_type = bin_info.get('card_type', 'Unknown')
            type_counts[card_type] = type_counts.get(card_type, 0) + 1
        
        return {
            'total_bins': total_bins,
            'by_type': type_counts
        }


if __name__ == "__main__":
    db = BINDatabase()
    
    print("🧪 Testing BIN Database...\n")
    
    test_card = "5154620012228852"
    db.add_bin(test_card, "visa")
    print(f"✅ Added BIN: {db.extract_bin(test_card)}")
    
    exists, info = db.check_bin(test_card)
    if exists:
        print(f"\n⚠️ BIN exists!")
        print(db.get_warning_message(info))
    
    db.add_bin(test_card, "visa")
    exists, info = db.check_bin(test_card)
    if exists:
        print(f"\n⚠️ BIN used again!")
        print(db.get_warning_message(info))
    
    stats = db.get_stats()
    print(f"\n📊 Database Stats:")
    print(f"Total BINs: {stats['total_bins']}")
    print(f"By Type: {stats['by_type']}")
