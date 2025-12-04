import os
import re
import time
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
from csv_helper import CSVHelper


class HealthMythCrawler:
    """
    衛福部國健署「保健闢謠」爬蟲

    職責：
    - 存取列表頁 / 內文頁
    - 解析文章 metadata + 內容
    - 依照是否已有 CSV 決定初始化或增量更新
    """

    BASE_URL = "https://www.hpa.gov.tw"
    TOPIC_LIST_URL = f"{BASE_URL}/Pages/TopicList.aspx?nodeid=127"
    DATE_PATTERN = re.compile(r"(\d{4}/\d{2}/\d{2})")

    def __init__(
        self,
        storage: CSVHelper,
        request_sleep_seconds: float = 0.8,
        timeout_seconds: int = 10,
    ):
        self.storage = storage
        self.request_sleep_seconds = request_sleep_seconds
        self.timeout_seconds = timeout_seconds

    # ---------- HTTP & 解析 ----------

    def _fetch_html(self, url: str) -> str:
        """發送 HTTP GET 取得 HTML 文字"""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=self.timeout_seconds)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        time.sleep(self.request_sleep_seconds)
        return resp.text

    def _parse_list_page(self, html: str) -> List[Dict]:
        """
        解析列表頁，回傳文章 metadata list：
        [
            {
                "pid": "18421",
                "title": "...",
                "url": "...",
                "publish_date": "2025/11/25",
                "update_date": "2025/07/04",
            },
            ...
        ]
        """
        soup = BeautifulSoup(html, "html.parser")
        articles: List[Dict] = []

        # 找出所有 Detail.aspx 連結
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "Pages/Detail.aspx" not in href:
                continue
            if "nodeid=127" not in href:
                continue

            title = a.get_text(strip=True)
            if not title:
                continue

            # 補成完整 URL
            if href.startswith("http"):
                url = href
            else:
                url = self.BASE_URL + href

            # 從 URL 抓出 pid
            pid_match = re.search(r"pid=(\d+)", href)
            pid = pid_match.group(1) if pid_match else None

            # 找到緊接著的「發布日期：... 更新日期：...」
            publish_date = self._extract_date(a, "發布日期")
            update_date = self._extract_date(a, "更新日期")

            articles.append(
                {
                    "pid": pid,
                    "title": title,
                    "url": url,
                    "publish_date": publish_date,
                    "update_date": update_date,
                }
            )

        # 以 pid 去重，維持出現順序
        seen = set()
        unique_articles: List[Dict] = []
        for art in articles:
            key = art["pid"] or art["url"]
            if key in seen:
                continue
            seen.add(key)
            unique_articles.append(art)

        return unique_articles

    def _extract_date(self, base_node, label: str) -> str:
        """
        從 base_node 之後的文字節點中，找到包含指定 label 的文字，
        然後用正規表示式抓出 yyyy/mm/dd 日期。
        """
        node = base_node.find_next(string=lambda s: s and label in s)
        if not node:
            return ""

        text = node.get_text(strip=True) if hasattr(node, "get_text") else str(node)
        # 支援「發布日期：」「更新日期:」等格式
        m = re.search(rf"{re.escape(label)}[:：]\s*{self.DATE_PATTERN.pattern}", text)
        return m.group(1) if m else ""

    def _extract_article_content(self, html: str, title: Optional[str] = None) -> str:
        """
        將文章內頁整頁文字取出，再用關鍵字做切分：
        - 從「發布日期：」後面開始
        - 到「上一則」或「下一則」之前
        """
        soup = BeautifulSoup(html, "html.parser")
        full_text = soup.get_text("\n")
        full_text = re.sub(r"\n{2,}", "\n", full_text)
        start_idx = 0
        idx = full_text.find("發布日期：")
        if idx != -1:
            next_newline = full_text.find("\n", idx)
            start_idx = next_newline + 1 if next_newline != -1 else idx
        elif title and title in full_text:
            start_idx = full_text.find(title) + len(title)

        end_idx = full_text.find("上一則", start_idx)
        if end_idx == -1:
            end_idx = full_text.find("下一則", start_idx)
        if end_idx == -1:
            end_idx = len(full_text)

        content = full_text[start_idx:end_idx].strip()
        lines = [line.strip() for line in content.splitlines()]
        meta_keywords = ["發布單位：", "發布日期：", "更新日期：", "點閱次數："]
        lines = [l for l in lines if not any(k in l for k in meta_keywords)]
        content = "\n".join(lines).strip()
        return content

    def _fetch_list_page(self, idx: int = 0) -> List[Dict]:
        """
        取得某一頁的列表資料：
        https://...TopicList.aspx?nodeid=127&idx={idx}
        """
        url = f"{self.TOPIC_LIST_URL}&idx={idx}"

        html = self._fetch_html(url)
        articles = self._parse_list_page(html)
        return articles

    # ---------- 業務流程：初始化與增量 ----------

    def initial_crawl_top_n(self, n: int = 10) -> None:
        """第一次執行：抓列表第 1 頁前 n 篇，含內文，寫入 CSV。"""
        print(f"=== 初始化：抓取保健闢謠前 {n} 篇文章 ===")
        articles = self._fetch_list_page(idx=0)
        target = articles[:n]

        rows: List[Dict] = []
        for art in target:
            print(f"抓取文章：{art['title']} ({art['url']})")
            detail_html = self._fetch_html(art["url"])
            content = self._extract_article_content(detail_html, title=art["title"])
            row = {
                "pid": art["pid"],
                "title": art["title"],
                "url": art["url"],
                "publish_date": art["publish_date"],
                "update_date": art["update_date"],
                "content": content,
            }
            rows.append(row)

        self.storage.save(rows)
        print(f"完成，已寫入 {self.storage.path}，共 {len(rows)} 筆。")

    def incremental_update(self, max_pages: int = 5) -> None:
        """
        增量更新：
        - 讀取既有 CSV 的 pid 集合
        - 由第 1 頁開始往後翻，找出新的 pid
        - 把新文章內文抓回來並 append
        """
        existing_rows = self.storage.load()
        existing_ids = {row.get("pid") for row in existing_rows if row.get("pid")}
        print(f"現有 CSV 筆數：{len(existing_rows)}，distinct pid：{len(existing_ids)}")

        new_articles: List[Dict] = []

        for idx in range(0, max_pages):
            print(f"檢查列表第 {idx + 1} 頁...")
            page_articles = self._fetch_list_page(idx=idx)
            if not page_articles:
                print("此頁無資料，停止。")
                break

            page_new = [a for a in page_articles if a["pid"] not in existing_ids]
            if not page_new:
                print("此頁所有文章都已在 CSV 中，停止往後翻頁。")
                break

            for a in page_new:
                print(f"發現新文章：{a['title']} ({a['url']})")
            new_articles.extend(page_new)

        if not new_articles:
            print("沒有發現新文章，CSV 無需更新。")
            return

        new_rows: List[Dict] = []
        for art in new_articles:
            print(f"抓取新文章內文：{art['title']}")
            detail_html = self._fetch_html(art["url"])
            content = self._extract_article_content(
                detail_html,
                title=art["title"],
            )
            row = {
                "pid": art["pid"],
                "title": art["title"],
                "url": art["url"],
                "publish_date": art["publish_date"],
                "update_date": art["update_date"],
                "content": content,
            }
            new_rows.append(row)

        self.storage.append(new_rows)
        print(f"增量更新完成，新增 {len(new_rows)} 筆。")

    # ---------- 入口 ----------

    def run(self, initial_n: int = 10, max_pages: int = 5) -> None:
        """
        根據是否存在 CSV，自動判斷：
        - 無 CSV → 初始化
        - 有 CSV → 增量更新
        """
        if not os.path.exists(self.storage.path):
            self.initial_crawl_top_n(n=initial_n)
        else:
            self.incremental_update(max_pages=max_pages)
