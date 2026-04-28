"""输出模块 - 格式化并保存分析报告"""
import os
import re
from datetime import datetime
from typing import Dict, Any, List
from config.settings import settings
from utils.logger import logger


class OutputManager:
    """管理分析报告的输出"""

    def __init__(self):
        self.output_dir = settings.output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save_match_analysis(self, match: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """保存单场比赛分析为 Markdown"""
        date_str = match["match_date"]
        home = self._safe_filename(match["home_team"])
        away = self._safe_filename(match["away_team"])
        filename = f"{date_str}_{home}_vs_{away}.md"
        filepath = os.path.join(self.output_dir, filename)

        content = analysis.get("content", "")
        if not content or content.startswith("分析失败"):
            logger.warning(f"跳过保存空/失败分析: {match['home_team']} vs {match['away_team']}")
            return ""

        # 构建完整的 Markdown 文件
        md_content = self._build_markdown(match, analysis)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"已保存分析: {filepath}")
        return filepath

    def save_daily_summary(self, date_str: str, summary: str, match_count: int) -> str:
        """保存每日总览"""
        filename = f"{date_str}_总览.md"
        filepath = os.path.join(self.output_dir, filename)

        header = f"""# ⚽ {date_str} 足球赛事总览

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 今日共分析 {match_count} 场比赛

---

"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(header + summary)

        logger.info(f"已保存每日总览: {filepath}")
        return filepath

    def _build_markdown(self, match: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """构建完整 Markdown 内容"""
        meta = f"""---
赛事: {match['competition']}
对阵: {match['home_team']} vs {match['away_team']}
比赛时间: {match['match_date']} {match.get('match_time', '')}
预测比分: {analysis.get('predicted_score', 'N/A')}
方向判断: {analysis.get('prediction_direction', 'N/A')}
信心指数: {analysis.get('confidence', 'N/A')}
AI模型: {analysis.get('model_used', 'N/A')}
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
---

# {match['competition']} | {match['home_team']} vs {match['away_team']}

> 🗓️ 比赛时间: {match['match_date']} {match.get('match_time', '')}

"""
        return meta + analysis.get("content", "")

    def _safe_filename(self, name: str) -> str:
        """将名称转换为安全文件名"""
        # 替换特殊字符
        safe = re.sub(r'[\\/*?":<>|]', "", name)
        safe = safe.replace(" ", "_")
        return safe[:50]

    def list_outputs(self) -> List[str]:
        """列出所有输出文件"""
        files = []
        if os.path.exists(self.output_dir):
            for f in sorted(os.listdir(self.output_dir)):
                if f.endswith(".md"):
                    files.append(f)
        return files
