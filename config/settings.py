"""项目配置管理"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    # API Keys
    openrouter_api_key: str = ""
    football_data_api_key: str = ""

    # Paths
    database_path: str = str(PROJECT_ROOT / "data" / "match_dianping.db")
    output_dir: str = str(PROJECT_ROOT / "output")

    # Logging
    log_level: str = "INFO"

    # Crawler
    request_delay: float = 1.5
    max_articles_per_match: int = 5
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    # OpenRouter LLM
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "deepseek/deepseek-chat"  # 性价比最好的中文模型
    openrouter_referer: str = "https://github.com/TongzheZhang/match_dianping"
    openrouter_title: str = "MatchDianping"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 8192

    # Football Data API
    football_data_base_url: str = "https://api.football-data.org/v4"

    # Target competitions (五大联赛 + 欧冠)
    target_competitions: list[int] = [
        2021,  # 英超 Premier League
        2014,  # 西甲 La Liga
        2019,  # 意甲 Serie A
        2002,  # 德甲 Bundesliga
        2015,  # 法甲 Ligue 1
        2001,  # 欧冠 Champions League
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
