#!/usr/bin/env python3
"""基础测试"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """测试所有模块是否能正常导入"""
    try:
        from config.settings import settings
        from core.database import init_db
        from modules.match_discovery import MatchDiscovery
        from modules.data_enhancer import DataEnhancer
        from modules.crawler import MatchCrawler
        from modules.ai_processor import AIProcessor
        from modules.output import OutputManager
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_database():
    """测试数据库初始化"""
    try:
        from core.database import init_db
        init_db()
        print("✅ 数据库初始化成功")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False


if __name__ == "__main__":
    print("运行基础测试...\n")
    results = []
    results.append(("模块导入", test_imports()))
    results.append(("数据库初始化", test_database()))

    print("\n" + "="*40)
    print("测试结果:")
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
