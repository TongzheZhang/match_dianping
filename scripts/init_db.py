#!/usr/bin/env python3
"""初始化数据库"""
import sys
from pathlib import Path

# 将项目根目录加入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import init_db

if __name__ == "__main__":
    init_db()
    print("数据库初始化完成！")
