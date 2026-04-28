"""数据增强模块 - 补充球队数据、战绩、伤停等"""
from typing import Dict, Any, List
from modules.match_discovery import MatchDiscovery
from utils.logger import logger
from utils.helpers import safe_get


class DataEnhancer:
    """为比赛补充实时数据"""

    def __init__(self):
        self.discovery = MatchDiscovery()

    def enhance(self, match: Dict[str, Any]) -> str:
        """为单场比赛生成补充数据文本"""
        parts = []
        comp_id = int(match.get("competition_code", 0))
        home_id = match.get("home_team_id", 0)
        away_id = match.get("away_team_id", 0)
        home_name = match["home_team"]
        away_name = match["away_team"]

        # 1. 积分榜信息
        if comp_id:
            standings_text = self._get_standings_info(comp_id, home_name, away_name)
            if standings_text:
                parts.append(f"## 积分榜情况\n{standings_text}\n")

        # 2. 近期战绩
        if home_id and away_id:
            home_recent = self._format_recent_matches(
                self.discovery.get_team_recent_matches(home_id), home_name
            )
            away_recent = self._format_recent_matches(
                self.discovery.get_team_recent_matches(away_id), away_name
            )
            if home_recent:
                parts.append(f"## {home_name} 近5场\n{home_recent}\n")
            if away_recent:
                parts.append(f"## {away_name} 近5场\n{away_recent}\n")

        # 3. 历史交锋
            h2h = self.discovery.get_head_to_head(home_id, away_id)
            h2h_text = self._format_h2h(h2h, home_name, away_name)
            if h2h_text:
                parts.append(f"## 近5次交锋\n{h2h_text}\n")

        return "\n".join(parts) if parts else "暂无详细数据补充。"

    def _get_standings_info(self, comp_id: int, home: str, away: str) -> str:
        """从积分榜提取两队排名"""
        data = self.discovery.get_standings(comp_id)
        standings = data.get("standings", [])
        if not standings:
            return ""

        # 取总积分榜（可能是第一个）
        table = None
        for s in standings:
            if s.get("type") == "TOTAL":
                table = s.get("table", [])
                break
        if not table and standings:
            table = standings[0].get("table", [])

        if not table:
            return ""

        home_info = None
        away_info = None

        for row in table:
            team_name = safe_get(row, "team", "name", default="")
            if team_name == home:
                home_info = row
            elif team_name == away:
                away_info = row

        lines = []
        if home_info:
            lines.append(
                f"- {home}: 排名 {home_info.get('position')}，"
                f"{home_info.get('won')}胜{home_info.get('draw')}平{home_info.get('lost')}负，"
                f"进{home_info.get('goalsFor')}失{home_info.get('goalsAgainst')}，"
                f"积分 {home_info.get('points')}"
            )
        if away_info:
            lines.append(
                f"- {away}: 排名 {away_info.get('position')}，"
                f"{away_info.get('won')}胜{away_info.get('draw')}平{away_info.get('lost')}负，"
                f"进{away_info.get('goalsFor')}失{away_info.get('goalsAgainst')}，"
                f"积分 {away_info.get('points')}"
            )

        return "\n".join(lines)

    def _format_recent_matches(self, matches: List[Dict], team_name: str) -> str:
        """格式化近期战绩"""
        if not matches:
            return ""
        lines = []
        for m in matches:
            home = safe_get(m, "homeTeam", "name", default="")
            away = safe_get(m, "awayTeam", "name", default="")
            home_score = safe_get(m, "score", "fullTime", "home", default="?")
            away_score = safe_get(m, "score", "fullTime", "away", default="?")
            date = m.get("utcDate", "")[:10]
            is_home = home == team_name
            result = "平"
            if home_score != "?" and away_score != "?":
                if is_home:
                    result = "胜" if home_score > away_score else ("负" if home_score < away_score else "平")
                else:
                    result = "胜" if away_score > home_score else ("负" if away_score < home_score else "平")
            lines.append(f"- {date} {home} {home_score}-{away_score} {away} ({result})")
        return "\n".join(lines)

    def _format_h2h(self, matches: List[Dict], home_name: str, away_name: str) -> str:
        """格式化历史交锋"""
        if not matches:
            return ""
        lines = []
        for m in matches:
            home = safe_get(m, "homeTeam", "name", default="")
            away = safe_get(m, "awayTeam", "name", default="")
            home_score = safe_get(m, "score", "fullTime", "home", default="?")
            away_score = safe_get(m, "score", "fullTime", "away", default="?")
            date = m.get("utcDate", "")[:10]
            comp = safe_get(m, "competition", "name", default="")
            lines.append(f"- {date} [{comp}] {home} {home_score}-{away_score} {away}")
        return "\n".join(lines)
