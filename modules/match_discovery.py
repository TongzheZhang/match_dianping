"""比赛发现模块 - 从 football-data.org 获取赛程，支持网络搜索备用"""
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
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

        # 如果 football-data API 全部失败，尝试网络搜索备用
        if not all_matches:
            logger.info("football-data API 不可用，尝试网络搜索获取焦点比赛...")
            all_matches = self._search_web_matches(date_from)

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

    def get_demo_matches(self) -> List[Dict[str, Any]]:
        """获取演示用比赛列表（用于测试 AI 链路）"""
        today = datetime.now().strftime("%Y-%m-%d")
        demos = [
            {
                "id": generate_id("demo", "曼城", "利物浦", today),
                "match_api_id": 0,
                "competition": "英超",
                "competition_code": "2021",
                "home_team": "Manchester City",
                "away_team": "Liverpool",
                "home_team_id": 65,
                "away_team_id": 64,
                "match_date": today,
                "match_time": "20:30",
                "status": "SCHEDULED",
            },
            {
                "id": generate_id("demo", "皇马", "巴萨", today),
                "match_api_id": 0,
                "competition": "西甲",
                "competition_code": "2014",
                "home_team": "Real Madrid",
                "away_team": "Barcelona",
                "home_team_id": 86,
                "away_team_id": 81,
                "match_date": today,
                "match_time": "22:00",
                "status": "SCHEDULED",
            },
            {
                "id": generate_id("demo", "拜仁", "多特", today),
                "match_api_id": 0,
                "competition": "德甲",
                "competition_code": "2002",
                "home_team": "Bayern Munich",
                "away_team": "Borussia Dortmund",
                "home_team_id": 5,
                "away_team_id": 4,
                "match_date": today,
                "match_time": "00:30",
                "status": "SCHEDULED",
            },
        ]
        logger.info(f"使用演示模式: {len(demos)} 场焦点比赛")
        return demos

    def _search_web_matches(self, date_str: str) -> List[Dict[str, Any]]:
        """通过网络搜索获取焦点比赛（备用方案）"""
        matches = []
        queries = [
            f"football fixtures {date_str}",
            f"soccer matches today premier league champions league",
        ]

        for query in queries:
            try:
                url = "https://html.duckduckgo.com/html/"
                resp = requests.post(
                    url,
                    data={"q": query, "kl": "us-en"},
                    headers={"User-Agent": settings.user_agent},
                    timeout=15,
                )
                soup = BeautifulSoup(resp.text, "html.parser")

                for result in soup.select(".result")[:8]:
                    a = result.select_one(".result__a")
                    if not a:
                        continue
                    title = a.get_text(strip=True)
                    # 尝试从标题提取比赛信息
                    match_info = self._parse_match_from_title(title, date_str)
                    if match_info:
                        matches.append(match_info)
                time.sleep(1)
            except Exception as e:
                logger.debug(f"搜索失败: {e}")

        return matches

    def _parse_match_from_title(self, title: str, date_str: str) -> Dict[str, Any] | None:
        """从搜索标题解析比赛信息"""
        # 常见格式: "Team A vs Team B" / "Team A v Team B" / "Team A - Team B"
        patterns = [
            r'([A-Za-z\s]+?)\s+(?:vs|v|VS|–|-)\s+([A-Za-z\s]+?)(?:\s*[\|:\-–]|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                home = match.group(1).strip()
                away = match.group(2).strip()
                if len(home) > 2 and len(away) > 2 and home != away:
                    return {
                        "id": generate_id(home, away, date_str),
                        "match_api_id": 0,
                        "competition": "未知联赛",
                        "competition_code": "0",
                        "home_team": home,
                        "away_team": away,
                        "home_team_id": 0,
                        "away_team_id": 0,
                        "match_date": date_str,
                        "match_time": "",
                        "status": "SCHEDULED",
                    }
        return None

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
