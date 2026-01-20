"""
Import utilities - Parsers for dates, currency, email
PASO 6 - Excel Import
"""
import re
from datetime import datetime, date
from typing import Optional, Tuple


def parse_date(value: any) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse date from various formats to ISO (YYYY-MM-DD)
    
    Returns: (parsed_date_str, error_message)
    """
    if not value:
        return None, None
    
    # If already a date object
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d'), None
    
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d'), None
    
    # If string, try various formats
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None, None
        
        # Try ISO format first
        try:
            dt = datetime.strptime(value, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d'), None
        except:
            pass
        
        # Try DD/MM/YYYY
        try:
            dt = datetime.strptime(value, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d'), None
        except:
            pass
        
        # Try DD-MM-YYYY
        try:
            dt = datetime.strptime(value, '%d-%m-%Y')
            return dt.strftime('%Y-%m-%d'), None
        except:
            pass
        
        # Try YYYY/MM/DD
        try:
            dt = datetime.strptime(value, '%Y/%m/%d')
            return dt.strftime('%Y-%m-%d'), None
        except:
            pass
        
        return None, f"Invalid date format: {value}"
    
    return None, f"Unexpected date type: {type(value)}"


def parse_month(value: any) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse month from various formats to YYYY-MM
    
    Returns: (parsed_month_str, error_message)
    """
    if not value:
        return None, None
    
    # If already datetime
    if isinstance(value, (date, datetime)):
        return value.strftime('%Y-%m'), None
    
    # If string
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None, None
        
        # Try YYYY-MM
        if re.match(r'^\d{4}-\d{2}$', value):
            return value, None
        
        # Try MM/YYYY
        match = re.match(r'^(\d{1,2})/(\d{4})$', value)
        if match:
            month, year = match.groups()
            return f"{year}-{int(month):02d}", None
        
        # Try YYYY/MM
        match = re.match(r'^(\d{4})/(\d{1,2})$', value)
        if match:
            year, month = match.groups()
            return f"{year}-{int(month):02d}", None
        
        return None, f"Invalid month format: {value}"
    
    return None, f"Unexpected month type: {type(value)}"


def parse_currency(value: any) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse currency value to float
    
    Accepts: "50.000,00", "50000.00", "50,000.00", etc
    Returns: (parsed_value, error_message)
    """
    if not value:
        return None, None
    
    # If already numeric
    if isinstance(value, (int, float)):
        return float(value), None
    
    # If string
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None, None
        
        # Remove currency symbols
        value = value.replace('€', '').replace('$', '').strip()
        
        # Handle European format (1.234,56 -> 1234.56)
        if ',' in value and '.' in value:
            if value.rindex(',') > value.rindex('.'):
                # European: 1.234,56
                value = value.replace('.', '').replace(',', '.')
            else:
                # US: 1,234.56
                value = value.replace(',', '')
        elif ',' in value:
            # Could be European 1234,56 or US 1,234
            if re.match(r'^\d{1,3}(,\d{3})+$', value):
                # US format with commas: 1,234 or 1,234,567
                value = value.replace(',', '')
            else:
                # European decimal: 1234,56
                value = value.replace(',', '.')
        
        # Try to convert
        try:
            parsed = float(value)
            return parsed, None
        except ValueError:
            return None, f"Invalid currency format: {value}"
    
    return None, f"Unexpected currency type: {type(value)}"


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format
    
    Returns: (is_valid, error_message)
    """
    if not email:
        return False, "Email is empty"
    
    email = email.strip()
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email):
        return True, None
    
    return False, f"Invalid email format: {email}"


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate phone format (basic)
    
    Returns: (is_valid, error_message)
    """
    if not phone:
        return False, "Phone is empty"
    
    phone = phone.strip()
    
    # Remove common separators
    clean = re.sub(r'[\s\-\.\(\)]', '', phone)
    
    # Check if it's mostly digits (allow + at start)
    if re.match(r'^\+?\d{9,15}$', clean):
        return True, None
    
    return False, f"Invalid phone format: {phone}"


def safe_str(value: any) -> Optional[str]:
    """Convert value to string safely, handling None and stripping"""
    if value is None or value == '':
        return None
    
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    
    return str(value).strip()


def safe_float(value: any) -> Optional[float]:
    """Convert value to float safely"""
    if value is None or value == '':
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return float(value)
        except:
            return None
    
    return None
