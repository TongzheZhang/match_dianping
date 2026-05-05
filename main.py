#!/usr/bin/env python3
"""
足球彩经智能采集与翻译系统 - 主入口

使用方法:
    python main.py                    # 分析未来2天的所有比赛
    python main.py --days 1           # 只分析明天
    python main.py --competition 2021 # 只分析英超 (2021)
    python main.py --match "曼联 vs 利物浦" # 分析指定比赛
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.database import init_db
from modules.match_discovery import MatchDiscovery
from modules.data_enhancer import DataEnhancer
from modules.crawler import MatchCrawler
from modules.ai_processor import AIProcessor
from modules.output import OutputManager
from utils.logger import logger
from config.settings import settings


def parse_args():
    parser = argparse.ArgumentParser(description="足球彩经智能分析系统")
    parser.add_argument("--days", type=int, default=2, help="提前分析天数 (默认2)")
    parser.add_argument("--competition", type=str, default=None, help="指定联赛代码 (如2021=英超)")
    parser.add_argument("--match", type=str, default=None, help="指定比赛名称 (如'曼联 vs 利物浦')")
    parser.add_argument("--max-articles", type=int, default=5, help="每场比赛采集文章数")
    parser.add_argument("--init-db", action="store_true", help="仅初始化数据库")
    parser.add_argument("--skip-ai", action="store_true", help="跳过AI分析（仅采集数据）")
    parser.add_argument("--demo", action="store_true", help="演示模式：使用预定义焦点比赛测试AI链路")
    return parser.parse_args()


def check_api_keys():
    """检查必要的API密钥"""
    missing = []
    if not settings.openrouter_api_key:
        missing.append("OPENROUTER_API_KEY")
    if not settings.football_data_api_key:
        missing.append("FOOTBALL_DATA_API_KEY (可选，但强烈建议配置)")

    if missing:
        logger.warning(f"缺少环境变量: {', '.join(missing)}")
        logger.warning("请复制 .env.example 为 .env 并填入你的 API Key")
        if "OPENROUTER_API_KEY" in missing:
            logger.error("OPENROUTER_API_KEY 是必需的，程序无法继续")
            return False
    return True


def main():
    args = parse_args()

    # 初始化数据库
    init_db()

    if args.init_db:
        print("数据库初始化完成")
        return

    if not check_api_keys():
        sys.exit(1)

    # 初始化模块
    discovery = MatchDiscovery()
    enhancer = DataEnhancer()
    crawler = MatchCrawler()
    ai = AIProcessor()
    output = OutputManager()

    # 1. 发现比赛
    if args.demo:
        print("\n🎮 演示模式：使用预定义焦点比赛")
        matches = discovery.get_demo_matches()
    else:
        print(f"\n🔍 正在发现未来 {args.days} 天的比赛...")
        matches = discovery.get_matches(days_ahead=args.days)

    if not matches:
        print("未找到符合条件的比赛。")
        return

    # 筛选
    if args.competition:
        matches = [m for m in matches if m.get("competition_code") == args.competition]
    if args.match:
        # 简单模糊匹配
        matches = [
            m for m in matches
            if args.match.split("vs")[0].strip().lower() in m["home_team"].lower()
            or args.match.split("vs")[-1].strip().lower() in m["away_team"].lower()
        ]

    print(f"📋 共发现 {len(matches)} 场待分析比赛:\n")
    for m in matches:
        print(f"  • [{m['competition']}] {m['home_team']} vs {m['away_team']} ({m['match_date']})")
    print()

    if args.skip_ai:
        print("--skip-ai 已启用，跳过AI分析。")
        return

    # 2. 逐场分析
    analysis_contents = []
    analyzed_count = 0

    for i, match in enumerate(matches, 1):
        print(f"\n{'='*60}")
        print(f"📌 [{i}/{len(matches)}] {match['home_team']} vs {match['away_team']}")
        print(f"{'='*60}")

        try:
            # 2a. 数据增强
            print("  📊 获取球队数据...", end=" ")
            team_data = enhancer.enhance(match)
            print("✅")

            # 2b. 采集文章
            print(f"  🌐 搜索赛前分析文章...", end=" ")
            articles = crawler.search_and_collect(
                match["home_team"],
                match["away_team"],
                match["competition"],
                max_articles=args.max_articles,
            )
            print(f"✅ (采集到 {len(articles)} 篇)")

            if not articles and not team_data.strip():
                print("  ⚠️ 未找到任何数据，跳过")
                continue

            # 2c. AI分析
            print("  🤖 调用 Kimi AI 分析中...", end=" ")
            analysis = ai.analyze_match(match, articles, team_data)
            print("✅")

            # 2d. 保存
            filepath = output.save_match_analysis(match, analysis)
            if filepath:
                analyzed_count += 1
                analysis_contents.append(analysis["content"])
                print(f"  💾 已保存: {Path(filepath).name}")
            else:
                print("  ⚠️ 保存失败或内容为空")

        except Exception as e:
            logger.exception(f"处理比赛失败: {e}")
            print(f"  ❌ 错误: {e}")
            continue

    # 3. 生成每日总览
    if analysis_contents:
        print(f"\n{'='*60}")
        print("📝 生成每日赛事总览...")
        date_str = matches[0]["match_date"] if matches else ""
        summary = ai.generate_daily_summary(analysis_contents)
        output.save_daily_summary(date_str, summary, analyzed_count)
        print("✅ 总览已生成")

    # 4. 完成
    print(f"\n{'='*60}")
    print(f"🎉 完成! 成功分析 {analyzed_count}/{len(matches)} 场比赛")
    print(f"📁 输出目录: {settings.output_dir}")
    files = output.list_outputs()
    if files:
        print(f"\n生成的文件:")
        for f in files[-10:]:  # 显示最近10个
            print(f"  • {f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
