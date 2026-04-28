"""比赛发现模块 - 从 football-data.org 获取赛程"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from config.settings import settings
from utils.logger import logger
from utils.helpers import generate_id, safe_get


class MatchDiscovery:
    """发现并获取焦点赛事"""

    COMPETITION_NAMES = {
        2021: "英超",
        2014: "西甲",
        2019: "意甲",
        2002: "德甲",
        2015: "法甲",
        2001: "欧冠",
    }

    def __init__(self):
        self.api_key = settings.football_data_api_key
        self.base_url = settings.football_data_base_url
        self.headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.user_agent,
            **self.headers,
        })

    def get_matches(self, days_ahead: int = 2) -> List[Dict[str, Any]]:
        """获取未来 N 天的比赛列表"""
        today = datetime.now()
        date_from = today.strftime("%Y-%m-%d")
        date_to = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        all_matches = []

        for comp_id in settings.target_competitions:
            try:
                matches = self._fetch_competition_matches(
                    comp_id, date_from, date_to
                )
                all_matches.extend(matches)
                time.sleep(0.5)  # 免费版限速
            except Exception as e:
                logger.warning(f"获取联赛 {comp_id} 赛程失败: {e}")

        # 去重并按时间排序
        seen = set()
        unique_matches = []
        for m in all_matches:
            key = (m["home_team"], m["away_team"], m["match_date"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(m)

        unique_matches.sort(key=lambda x: x["match_date"])
        logger.info(f"发现 {len(unique_matches)} 场待分析比赛")
        return unique_matches

    def _fetch_competition_matches(
        self, comp_id: int, date_from: str, date_to: str
    ) -> List[Dict[str, Any]]:
        """获取单个联赛的比赛"""
        url = f"{self.base_url}/competitions/{comp_id}/matches"
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "status": "SCHEDULED",  # 只取未进行的比赛
        }

        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        matches = []
        for match in data.get("matches", []):
            match_info = {
                "id": generate_id(
                    match.get("id"),
                    match.get("homeTeam", {}).get("name"),
                    match.get("awayTeam", {}).get("name"),
                ),
                "match_api_id": match.get("id"),
                "competition": self.COMPETITION_NAMES.get(
                    comp_id, safe_get(match, "competition", "name", default="未知")
                ),
                "competition_code": str(comp_id),
                "home_team": safe_get(match, "homeTeam", "name", default=""),
                "away_team": safe_get(match, "awayTeam", "name", default=""),
                "home_team_id": safe_get(match, "homeTeam", "id", default=0),
                "away_team_id": safe_get(match, "awayTeam", "id", default=0),
                "match_date": match.get("utcDate", "")[:10],
                "match_time": match.get("utcDate", "")[11:16],
                "status": match.get("status", "SCHEDULED"),
            }
            matches.append(match_info)

        return matches

    def get_standings(self, comp_id: int) -> Dict[str, Any]:
        """获取联赛积分榜"""
        url = f"{self.base_url}/competitions/{comp_id}/standings"
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"获取积分榜失败: {e}")
            return {}

    def get_team_recent_matches(self, team_id: int, limit: int = 5) -> List[Dict]:
        """获取球队近期比赛"""
        url = f"{self.base_url}/teams/{team_id}/matches"
        params = {"limit": limit, "status": "FINISHED"}
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get("matches", [])
        except Exception as e:
            logger.warning(f"获取球队近期战绩失败 (team_id={team_id}): {e}")
            return []

    def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 5) -> List[Dict]:
        """获取两队历史交锋"""
        url = f"{self.base_url}/teams/{team1_id}/matches"
        params = {"limit": 20}
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            matches = []
            for m in data.get("matches", []):
                home_id = safe_get(m, "homeTeam", "id", default=0)
                away_id = safe_get(m, "awayTeam", "id", default=0)
                if (home_id == team2_id or away_id == team2_id) and m.get("status") == "FINISHED":
                    matches.append(m)
                if len(matches) >= limit:
                    break
            return matches
        except Exception as e:
            logger.warning(f"获取历史交锋失败: {e}")
            return []
