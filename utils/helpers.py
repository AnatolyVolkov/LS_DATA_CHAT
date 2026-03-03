# utils/helpers.py
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
from typing import Dict, Any

def format_date(date_str):
    """Format date for display"""
    if isinstance(date_str, datetime):
        return date_str.strftime('%d.%m.%Y %H:%M')
    return date_str

def safe_json_dumps(obj):
    """Safe JSON serialization"""
    def default_handler(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, timedelta):
            return str(o)
        if isinstance(o, pd.Timestamp):
            return o.isoformat()
        if hasattr(o, '__dict__'):
            return str(o)
        return None
    
    return json.dumps(obj, default=default_handler, ensure_ascii=False)

def hash_query(query: str) -> str:
    """Create hash of query for caching"""
    return hashlib.md5(query.encode()).hexdigest()

def validate_table_name(table: str) -> bool:
    """Validate table name to prevent SQL injection"""
    allowed_tables = [
        'client', 'lic_key', 'key_assignment', 'client_contract',
        'feature', 'client_document_feature', 'app', 'app_version',
        'filial', 'partner', 'contract_type', 'ci_type'
    ]
    return table in allowed_tables

def parse_natural_date(date_str: str) -> datetime:
    """Parse natural language date"""
    today = datetime.now()
    
    date_str = date_str.lower().strip()
    
    if 'сегодня' in date_str:
        return today
    elif 'вчера' in date_str:
        return today - timedelta(days=1)
    elif 'завтра' in date_str:
        return today + timedelta(days=1)
    elif 'неделю' in date_str:
        return today - timedelta(weeks=1)
    elif 'месяц' in date_str:
        return today - timedelta(days=30)
    elif 'год' in date_str:
        return today - timedelta(days=365)
    
    return today