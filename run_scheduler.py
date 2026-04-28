#!/usr/bin/env python3
"""
定时任务入口 - 每天自动执行分析

使用方法:
    python run_scheduler.py           # 前台运行
    python run_scheduler.py --daemon  # 后台模式 (Linux/Mac)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.logger import logger


def job():
    """定时执行的分析任务"""
    logger.info("定时任务启动...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "main.py", "--days", "1"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent),
    )
    logger.info(result.stdout)
    if result.stderr:
        logger.error(result.stderr)
    logger.info("定时任务结束")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="后台运行")
    parser.add_argument("--hour", type=int, default=9, help="每日执行小时 (默认9点)")
    parser.add_argument("--minute", type=int, default=0, help="每日执行分钟 (默认0分)")
    args = parser.parse_args()

    scheduler = BlockingScheduler()
    trigger = CronTrigger(hour=args.hour, minute=args.minute)
    scheduler.add_job(job, trigger, id="daily_match_analysis")

    print(f"⏰ 定时任务已设置: 每天 {args.hour:02d}:{args.minute:02d} 执行")
    print("按 Ctrl+C 停止")
    logger.info(f"Scheduler started, will run daily at {args.hour:02d}:{args.minute:02d}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("\n定时任务已停止")


if __name__ == "__main__":
    main()
