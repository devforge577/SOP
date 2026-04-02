"""
Utility functions and helpers for POS System
"""

# You can add utility functions here as needed

def format_currency(amount: float) -> str:
    """Format a number as currency"""
    return f"GHS {amount:,.2f}"

def format_date(date_str: str, format_type: str = "short") -> str:
    """Format date strings for display"""
    if not date_str:
        return ""
    if format_type == "short":
        return date_str[:10] if len(date_str) > 10 else date_str
    return date_str

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Basic phone validation"""
    import re
    # Allow digits, spaces, dashes, and plus sign
    pattern = r'^[\d\s\-+]+$'
    return bool(re.match(pattern, phone)) and len(phone) >= 8

__all__ = [
    'format_currency',
    'format_date',
    'validate_email',
    'validate_phone'
]