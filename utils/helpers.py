"""通用工具函数"""
import re
import hashlib
from datetime import datetime, timedelta
from typing import Optional


def clean_text(text: str) -> str:
    """清洗文本：去除多余空白、特殊字符"""
    if not text:
        return ""
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 去除零宽字符
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    return text.strip()


def truncate_text(text: str, max_length: int = 8000) -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n\n[内容已截断...]"


def generate_id(*args) -> str:
    """基于输入生成唯一ID"""
    content = "|".join(str(a) for a in args)
    return hashlib.md5(content.encode()).hexdigest()[:16]


def format_date(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d") -> str:
    """格式化日期"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def get_date_range(days: int = 1) -> tuple[str, str]:
    """获取从今天起 N 天的日期范围"""
    today = datetime.now()
    end = today + timedelta(days=days)
    return today.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def safe_get(d: dict, *keys, default=None):
    """安全地从嵌套字典中获取值"""
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d
