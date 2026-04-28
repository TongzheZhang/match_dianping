"""爬虫模块 - 搜索和采集赛前分析文章"""
import time
import re
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
from config.settings import settings
from utils.logger import logger
from utils.helpers import clean_text, generate_id


class MatchCrawler:
    """采集足球赛前分析文章"""

    # 直接支持的赛前分析来源
    SOURCES = {
        "bbc": {
            "name": "BBC Sport",
            "search_url": "https://www.bbc.com/search?q={query}&page=1",
            "article_selector": "a[data-testid='internal-link']",
        },
        "espn": {
            "name": "ESPN",
            "search_url": "https://www.espn.com/search/_/q/{query}",
        },
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        self.delay = settings.request_delay

    def search_and_collect(
        self,
        home_team: str,
        away_team: str,
        competition: str,
        max_articles: int = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索并采集赛前分析文章。
        策略：
        1. 构造搜索关键词
        2. 尝试多个来源获取文章链接
        3. 抓取文章内容
        """
        if max_articles is None:
            max_articles = settings.max_articles_per_match

        query = f"{home_team} vs {away_team} preview prediction"
        logger.info(f"开始搜索文章: {query}")

        articles = []
        collected_urls = set()

        # 策略1: 使用 DuckDuckGo HTML 搜索（无需API Key）
        ddg_results = self._search_duckduckgo(query, max_results=max_articles + 3)
        for result in ddg_results:
            if len(articles) >= max_articles:
                break
            url = result.get("url", "")
            if not url or url in collected_urls:
                continue
            # 过滤掉非英文/低质量来源
            if self._is_valid_source(url):
                article = self._fetch_article(url, result.get("title", ""))
                if article and len(article.get("content", "")) > 300:
                    articles.append(article)
                    collected_urls.add(url)
                    logger.debug(f"采集文章: {article['title'][:60]}...")
            time.sleep(self.delay)

        # 策略2: 直接构造已知来源的URL尝试
        if len(articles) < max_articles // 2:
            fallback = self._try_known_sources(home_team, away_team)
            for article in fallback:
                if len(articles) >= max_articles:
                    break
                if article.get("url") not in collected_urls:
                    articles.append(article)
                    collected_urls.add(article["url"])

        logger.info(f"成功采集 {len(articles)} 篇文章")
        return articles

    def _search_duckduckgo(self, query: str, max_results: int = 8) -> List[Dict]:
        """使用 DuckDuckGo HTML 界面搜索"""
        results = []
        try:
            url = "https://html.duckduckgo.com/html/"
            resp = self.session.post(
                url,
                data={"q": query, "kl": "us-en"},
                timeout=20,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for result in soup.select(".result"):
                if len(results) >= max_results:
                    break
                a = result.select_one(".result__a")
                if not a:
                    continue
                title = a.get_text(strip=True)
                href = a.get("href", "")
                # DuckDuckGo 的链接是跳转链接，需要解析
                if href.startswith("//duckduckgo.com/l/?"):
                    # 提取真实URL
                    match = re.search(r'uddg=([^&]+)', href)
                    if match:
                        import urllib.parse
                        real_url = urllib.parse.unquote(match.group(1))
                    else:
                        continue
                else:
                    real_url = href

                snippet_elem = result.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                results.append({
                    "title": title,
                    "url": real_url,
                    "snippet": snippet,
                })
            time.sleep(self.delay)
        except Exception as e:
            logger.warning(f"DuckDuckGo 搜索失败: {e}")

        return results

    def _fetch_article(self, url: str, title: str = "") -> Dict[str, Any]:
        """抓取单篇文章内容"""
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # 提取标题
            if not title:
                title_tag = soup.find("title")
                title = title_tag.get_text(strip=True) if title_tag else "无标题"

            # 提取正文 - 使用多种策略
            content = self._extract_content(soup, url)

            if len(content) < 200:
                return None

            return {
                "id": generate_id(url),
                "title": clean_text(title),
                "url": url,
                "source": urlparse(url).netloc,
                "content": content,
                "publish_date": "",
            }
        except Exception as e:
            logger.debug(f"抓取文章失败 {url}: {e}")
            return None

    def _extract_content(self, soup: BeautifulSoup, url: str) -> str:
        """从网页提取正文内容"""
        # 移除脚本和样式
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # 策略1: 寻找 article 标签
        article = soup.find("article")
        if article:
            text = article.get_text(separator="\n", strip=True)
            if len(text) > 300:
                return clean_text(text)

        # 策略2: 寻找主要内容容器
        for selector in [
            "main", "[role='main']", ".article-body", ".story-body",
            ".content", "#content", ".post-content", ".entry-content",
        ]:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(separator="\n", strip=True)
                if len(text) > 300:
                    return clean_text(text)

        # 策略3: 按文本密度找最大段落集合
        paragraphs = soup.find_all("p")
        texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
        if texts:
            return clean_text("\n\n".join(texts))

        # 策略4: 退回到 body
        body = soup.find("body")
        if body:
            return clean_text(body.get_text(separator="\n", strip=True))

        return ""

    def _is_valid_source(self, url: str) -> bool:
        """判断是否为有效来源"""
        domain = urlparse(url).netloc.lower()
        # 排除社交媒体、视频、购物等
        blocked = [
            "youtube", "twitter", "x.com", "facebook", "instagram",
            "tiktok", "amazon", "ebay", "reddit", "pinterest",
            "linkedin", "google", "bing", "yahoo",
        ]
        for b in blocked:
            if b in domain:
                return False
        return True

    def _try_known_sources(self, home: str, away: str) -> List[Dict]:
        """尝试直接从已知来源获取"""
        articles = []
        # BBC 比赛页面格式尝试
        bbc_slugs = [
            f"https://www.bbc.com/sport/football",
        ]
        # 这些主要是备用，实际内容主要靠搜索获取
        return articles
