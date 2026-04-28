"""AI 处理模块 - 调用 Kimi API 进行翻译和分析"""
import os
from typing import Dict, Any, List
from openai import OpenAI
from config.settings import settings
from config.prompts import MATCH_ANALYSIS_PROMPT, SUMMARY_PROMPT
from utils.logger import logger
from utils.helpers import truncate_text


class AIProcessor:
    """使用 Kimi LLM 进行赛前分析"""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.kimi_api_key or os.getenv("KIMI_API_KEY", ""),
            base_url=settings.kimi_base_url,
        )
        self.model = settings.kimi_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

    def analyze_match(
        self,
        match: Dict[str, Any],
        articles: List[Dict[str, Any]],
        team_data: str,
    ) -> Dict[str, Any]:
        """分析单场比赛并生成中文彩经"""
        # 准备文章文本
        articles_text = self._format_articles(articles)

        # 构建 Prompt
        prompt = MATCH_ANALYSIS_PROMPT.format(
            competition=match["competition"],
            home_team=match["home_team"],
            away_team=match["away_team"],
            match_date=f"{match['match_date']} {match.get('match_time', '')}",
            team_data=team_data,
            articles=articles_text,
        )

        logger.info(f"开始AI分析: {match['home_team']} vs {match['away_team']}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的足球分析师和中文体育撰稿人。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            content = response.choices[0].message.content

            # 提取预测信息
            prediction = self._extract_prediction(content)

            return {
                "content": content,
                "predicted_score": prediction.get("score", ""),
                "prediction_direction": prediction.get("direction", ""),
                "confidence": prediction.get("confidence", "中"),
                "model_used": self.model,
            }
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return {
                "content": f"分析失败: {e}",
                "predicted_score": "",
                "prediction_direction": "",
                "confidence": "",
                "model_used": self.model,
            }

    def generate_daily_summary(self, analyses: List[str]) -> str:
        """生成今日赛事总览"""
        if not analyses:
            return "今日暂无分析数据。"

        combined = "\n\n---\n\n".join(analyses)
        # 控制总长度
        combined = truncate_text(combined, 12000)

        prompt = SUMMARY_PROMPT.format(all_analyses=combined)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个足球赛事综述专家。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"生成总览失败: {e}")
            return f"总览生成失败: {e}"

    def _format_articles(self, articles: List[Dict[str, Any]]) -> str:
        """格式化文章列表为文本"""
        if not articles:
            return "未找到相关赛前分析文章。"

        parts = []
        for i, article in enumerate(articles, 1):
            title = article.get("title", "无标题")
            source = article.get("source", "未知来源")
            content = article.get("content", "")
            # 每篇文章取前2000字
            content = truncate_text(content, 2000)
            parts.append(
                f"### 文章 {i}\n"
                f"**标题**: {title}\n"
                f"**来源**: {source}\n"
                f"**内容**:\n{content}\n"
            )
        return "\n".join(parts)

    def _extract_prediction(self, content: str) -> Dict[str, str]:
        """从分析内容中提取预测信息"""
        import re
        result = {"score": "", "direction": "", "confidence": "中"}

        # 提取比分预测 - 常见格式如 "比分预测：2:1" 或 "预测比分：2-1"
        score_patterns = [
            r'比分预测[：:]\s*([\d\-:\s,、]+)',
            r'预测比分[：:]\s*([\d\-:\s,、]+)',
        ]
        for pattern in score_patterns:
            match = re.search(pattern, content)
            if match:
                result["score"] = match.group(1).strip()[:50]
                break

        # 提取方向判断
        direction_keywords = ["主胜", "客胜", "平局", "让球", "大球", "小球"]
        for kw in direction_keywords:
            if kw in content:
                # 找包含关键词的句子
                sentences = re.split(r'[。！\n]', content)
                for s in sentences:
                    if kw in s and len(s) < 80:
                        result["direction"] = s.strip()[:50]
                        break
                if result["direction"]:
                    break

        # 置信度
        if "信心较高" in content or "高信心" in content:
            result["confidence"] = "高"
        elif "信心较低" in content or "难以判断" in content:
            result["confidence"] = "低"

        return result
