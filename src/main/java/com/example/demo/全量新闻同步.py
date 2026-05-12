# -*- coding: utf-8 -*-
"""
tongtech.com 新闻全量同步脚本

功能：
1. 从 https://www.tongtech.com/news/1.html 开始按页拉取全量新闻列表。
2. 逐条解析详情页并按 biz_id=md5(详情页URL) 写入 t_portal_context。
3. 数据库中已存在的重复新闻会更新正文、标题、发布时间、封面等字段，并恢复为正常状态。
4. 官网全量列表中不存在、但数据库中仍存在的同栏目官网新闻会做逻辑删除。

常用命令：
    python3 全量新闻同步.py
    python3 全量新闻同步.py --dry-run
    python3 全量新闻同步.py --crawl-only --max-pages 1 --detail-limit 1

依赖安装：
    pip install requests beautifulsoup4 lxml pymysql

数据库配置在本脚本内维护，也支持通过环境变量覆盖：
NEWS_DB_HOST、NEWS_DB_PORT、NEWS_DB_USER、NEWS_DB_PASSWORD、NEWS_DB_NAME。
"""

import argparse
import hashlib
import os
import re
import sys
import time
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.tongtech.com"
MYSQL_CONFIG = {
    "host": "10.10.80.52",
    "port": 3306,
    "user": "root",
    "password": "Golden!@#dftoms",
    "database": "tongframework_dev",
    "charset": "utf8mb4",
}

CREATE_BY = "1242684364872761344"
SECTION_ID = "26e1ac838e2241e6aec69d79fcaa745a"
CONTEXT_PUBLISHED = "1"
CONTEXT_AUTHOR = "超级管理员"
ENCLOSURE = "[]"
CONTEXT_SOURCE = "东方通官网"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

DEFAULT_ACTIVE_STATUS = os.getenv("NEWS_ACTIVE_STATUS", "0")
DEFAULT_DELETE_STATUS = os.getenv("NEWS_DELETE_STATUS", "1")
DEFAULT_PAGE_SLEEP = float(os.getenv("NEWS_PAGE_SLEEP", "0.5"))
DEFAULT_DETAIL_SLEEP = float(os.getenv("NEWS_DETAIL_SLEEP", "1.0"))
DEFAULT_EMPTY_PAGE_LIMIT = int(os.getenv("NEWS_EMPTY_PAGE_LIMIT", "1"))


def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def get_soup(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "lxml")
    except Exception as exc:
        print(f"请求失败: {url}, 错误: {exc}")
        return None


def build_mysql_config() -> Dict[str, object]:
    config = dict(MYSQL_CONFIG)
    config["host"] = os.getenv("NEWS_DB_HOST", str(config.get("host", "")))
    config["port"] = int(os.getenv("NEWS_DB_PORT", str(config.get("port", 3306))))
    config["user"] = os.getenv("NEWS_DB_USER", str(config.get("user", "")))
    config["password"] = os.getenv("NEWS_DB_PASSWORD", str(config.get("password", "")))
    config["database"] = os.getenv("NEWS_DB_NAME", str(config.get("database", "")))
    config["charset"] = os.getenv("NEWS_DB_CHARSET", str(config.get("charset", "utf8mb4")))
    return config


def get_page_url(page_no: int) -> str:
    return f"{BASE_URL}/news/{page_no}.html"


def normalize_title(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_news_date(pub_date: str) -> str:
    match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", pub_date or "")
    return match.group(1) if match else ""


def normalize_rich_text(html_content: str) -> str:
    if not html_content:
        return "<div></div>"

    soup = BeautifulSoup(html_content, "lxml")
    neirongxq = soup.find("div", class_="neirongxq") or soup

    for p in neirongxq.find_all("p"):
        style = p.get("style", "")
        base_style = (
            "box-sizing: border-box; margin: 0px; padding: 0px; font-size: 16px; "
            "white-space: normal; color: #222222; line-height: 1.75;"
        )
        if "text-align:justify" in style or "background-color:#FFFFFF" in style:
            base_style += " text-align:justify; background-color:#FFFFFF;"
        p["style"] = base_style

        if p.get_text(strip=True) == "":
            p.clear()
            p.append(BeautifulSoup("&nbsp;", "html.parser"))
            p["class"] = p.get("class", []) + ["empty-line"]

    for img in neirongxq.find_all("img"):
        img["class"] = img.get("class", []) + ["syl-page-img"]
        img["style"] = (
            "box-sizing: border-box; border: 0; vertical-align: middle; "
            "display: block; margin: 15px auto; max-width: 80%; height: auto;"
        )
        if img.get("src") and not img["src"].startswith(("http://", "https://")):
            img["src"] = urljoin(BASE_URL, img["src"])

    for div in neirongxq.find_all("div", class_="pgc-img"):
        div["style"] = (
            "box-sizing: border-box; margin: 18px 0; padding: 0; font-size: 16px; "
            "text-align: center; color: #222222;"
        )

    for br in neirongxq.find_all("br"):
        parent = br.parent
        if parent and parent.name == "p" and len(parent.contents) == 1:
            br.decompose()

    style_tag = soup.new_tag("style")
    style_tag.string = """
    .empty-line {
        height: 1.75em;
        line-height: 1.75;
    }
    .empty-line::before {
        content: "";
        display: block;
        height: 100%;
    }
    """
    neirongxq.insert(0, style_tag)

    return str(neirongxq)


def get_news_list(page_no: int) -> List[Dict[str, str]]:
    """获取指定分页的新闻列表。"""
    page_url = get_page_url(page_no)
    soup = get_soup(page_url)
    if not soup:
        raise RuntimeError(f"新闻列表页请求失败: {page_url}")

    items = soup.select(".gywm_news ul li")
    news_list = []

    for item in items:
        title_span = item.select_one(".biaoti2")
        main_title = normalize_title(title_span.get_text(strip=True) if title_span else "")

        sub_div = item.select_one(".wenzix")
        sub_title = sub_div.get_text(strip=True) if sub_div else ""

        more_a = item.select_one(".chakangengduo a")
        detail_url = urljoin(BASE_URL, more_a["href"]) if more_a and more_a.get("href") else ""

        date_span = item.select_one(".shijian2")
        pub_date = date_span.get_text(strip=True) if date_span else ""

        if main_title and detail_url:
            news_list.append(
                {
                    "biz_id": md5(detail_url),
                    "main_title": main_title,
                    "sub_title": sub_title,
                    "detail_url": detail_url,
                    "pub_date": pub_date,
                    "news_date": extract_news_date(pub_date),
                }
            )

    return news_list


def crawl_all_news(
    max_pages: int,
    page_sleep: float,
    empty_page_limit: int,
) -> Tuple[List[Dict[str, str]], bool]:
    """
    拉取全量新闻列表。

    返回值第二项表示是否完成全量抓取。设置 max_pages 时只适合调试，不能用于软删除。
    """
    all_news: List[Dict[str, str]] = []
    seen_biz_ids: Set[str] = set()
    empty_pages = 0
    page_no = 1

    while True:
        if max_pages and page_no > max_pages:
            print(f"已达到调试分页上限 max_pages={max_pages}，停止继续抓取")
            return all_news, False

        page_url = get_page_url(page_no)
        print(f"正在抓取新闻列表页: {page_url}")
        page_news = get_news_list(page_no)

        if not page_news:
            empty_pages += 1
            print(f"第 {page_no} 页未找到新闻，连续空页数: {empty_pages}/{empty_page_limit}")
            if empty_pages >= empty_page_limit:
                return all_news, True
        else:
            empty_pages = 0
            added = 0
            for news in page_news:
                if news["biz_id"] in seen_biz_ids:
                    continue
                seen_biz_ids.add(news["biz_id"])
                all_news.append(news)
                added += 1
            print(f"第 {page_no} 页找到 {len(page_news)} 条新闻，新增 {added} 条")

        page_no += 1
        if page_sleep > 0:
            time.sleep(page_sleep)


def parse_detail(detail_url: str, list_pub_date: str) -> Optional[Dict[str, str]]:
    soup = get_soup(detail_url)
    if not soup:
        return None

    raw_content = soup.select_one(".neirongxq")
    if not raw_content:
        for selector in (
            ".news-content",
            ".content",
            ".article-content",
            ".detail-content",
            ".main-content",
        ):
            raw_content = soup.select_one(selector)
            if raw_content:
                break

    if not raw_content:
        for div in soup.find_all("div"):
            text_length = len(div.get_text(strip=True))
            p_count = len(div.find_all("p"))
            if text_length > 200 or p_count > 2:
                raw_content = div
                break

    content_html = normalize_rich_text(str(raw_content)) if raw_content else "<div></div>"

    pub_time_str = list_pub_date
    detail_time_p = soup.select_one(".xinwenxiangqing_bt p")
    if detail_time_p:
        pub_time_str = detail_time_p.get_text(strip=True)

    pub_time = "1970-01-01 00:00:00"
    if pub_time_str:
        for pattern in (
            r"(\d{4}[-年]\d{1,2}[-月]\d{1,2})",
            r"(\d{4}/\d{1,2}/\d{1,2})",
            r"(\d{4}\.\d{1,2}\.\d{1,2})",
        ):
            match = re.search(pattern, pub_time_str)
            if not match:
                continue
            date_clean = (
                match.group(1)
                .replace("年", "-")
                .replace("月", "-")
                .replace("日", "")
                .replace("/", "-")
                .replace(".", "-")
            )
            try:
                pub_time = datetime.strptime(date_clean, "%Y-%m-%d").strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                break
            except ValueError:
                continue

    keywords_meta = soup.select_one('meta[name="keywords"]')
    keywords = keywords_meta["content"] if keywords_meta and keywords_meta.get("content") else ""

    img_soup = BeautifulSoup(content_html, "lxml")
    img = img_soup.select_one("img")
    pic_link = urljoin(detail_url, img["src"]) if img and img.get("src") else ""

    return {
        "published_time": pub_time,
        "content": content_html,
        "summary": "",
        "keywords": keywords,
        "source": CONTEXT_SOURCE,
        "pic_link": pic_link,
        "origin_url": detail_url,
    }


def parse_news_details(
    news_list: Sequence[Dict[str, str]],
    detail_sleep: float,
    detail_limit: int,
) -> Tuple[List[Dict[str, object]], List[Dict[str, str]]]:
    parsed_news: List[Dict[str, object]] = []
    failed_news: List[Dict[str, str]] = []

    target_news = news_list[:detail_limit] if detail_limit > 0 else news_list
    total = len(target_news)

    for index, news in enumerate(target_news, start=1):
        print(f"\n[{index}/{total}] 解析新闻详情: {news['main_title']}")
        print(f"详情页: {news['detail_url']}")

        detail_data = parse_detail(news["detail_url"], news["pub_date"])
        if detail_data:
            merged = dict(news)
            merged.update(detail_data)
            parsed_news.append(merged)
        else:
            failed_news.append(news)
            print(f"解析详情页失败: {news['detail_url']}")

        if detail_sleep > 0:
            time.sleep(detail_sleep)

    return parsed_news, failed_news


def iter_chunks(values: Sequence[str], chunk_size: int) -> Iterable[Sequence[str]]:
    for index in range(0, len(values), chunk_size):
        yield values[index : index + chunk_size]


def fetch_existing_news(conn) -> Dict[str, str]:
    sql = """
        SELECT biz_id, status
        FROM t_portal_context
        WHERE section_id = %s
          AND context_source = %s
          AND biz_id IS NOT NULL
    """
    with conn.cursor() as cur:
        cur.execute(sql, (SECTION_ID, CONTEXT_SOURCE))
        return {str(row[0]): "" if row[1] is None else str(row[1]) for row in cur.fetchall()}


def upsert_news(conn, parsed_news: Sequence[Dict[str, object]], active_status: str) -> int:
    if not parsed_news:
        return 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
        INSERT INTO `t_portal_context`(
            `biz_id`, `status`, `create_by`, `create_date`, `update_by`, `update_date`,
            `remarks`, `section_id`, `context_title`, `context_sub_title`,
            `context_keywords`, `context_source`, `context_summary`, `context_main`,
            `published_time`, `context_re_link`, `context_pic_link`, `context_published`,
            `context_author`, `context_author_id`, `enclosure`
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            NULL, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            `status` = VALUES(`status`),
            `update_by` = VALUES(`update_by`),
            `update_date` = VALUES(`update_date`),
            `section_id` = VALUES(`section_id`),
            `context_title` = VALUES(`context_title`),
            `context_sub_title` = VALUES(`context_sub_title`),
            `context_keywords` = VALUES(`context_keywords`),
            `context_source` = VALUES(`context_source`),
            `context_summary` = VALUES(`context_summary`),
            `context_main` = VALUES(`context_main`),
            `published_time` = VALUES(`published_time`),
            `context_re_link` = VALUES(`context_re_link`),
            `context_pic_link` = VALUES(`context_pic_link`),
            `context_published` = VALUES(`context_published`),
            `context_author` = VALUES(`context_author`),
            `context_author_id` = VALUES(`context_author_id`),
            `enclosure` = VALUES(`enclosure`)
    """

    params = []
    for news in parsed_news:
        params.append(
            (
                news["biz_id"],
                active_status,
                CREATE_BY,
                now,
                CREATE_BY,
                now,
                SECTION_ID,
                news["main_title"],
                news["sub_title"],
                news.get("keywords", ""),
                news.get("source") or CONTEXT_SOURCE,
                news.get("summary", ""),
                news.get("content", "<div></div>"),
                news.get("published_time", "1970-01-01 00:00:00"),
                news.get("origin_url", news["detail_url"]),
                news.get("pic_link", ""),
                CONTEXT_PUBLISHED,
                CONTEXT_AUTHOR,
                CREATE_BY,
                ENCLOSURE,
            )
        )

    with conn.cursor() as cur:
        cur.executemany(sql, params)

    return len(params)


def soft_delete_news(conn, biz_ids: Sequence[str], delete_status: str) -> int:
    if not biz_ids:
        return 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = 0
    with conn.cursor() as cur:
        for chunk in iter_chunks(list(biz_ids), 500):
            placeholders = ", ".join(["%s"] * len(chunk))
            sql = f"""
                UPDATE t_portal_context
                SET status = %s,
                    update_by = %s,
                    update_date = %s
                WHERE section_id = %s
                  AND context_source = %s
                  AND (status IS NULL OR status <> %s)
                  AND biz_id IN ({placeholders})
            """
            params = [delete_status, CREATE_BY, now, SECTION_ID, CONTEXT_SOURCE, delete_status]
            params.extend(chunk)
            total += cur.execute(sql, params)

    return total


def sync_database(
    source_biz_ids: Set[str],
    parsed_news: Sequence[Dict[str, object]],
    dry_run: bool,
    no_delete: bool,
    allow_delete: bool,
    active_status: str,
    delete_status: str,
) -> None:
    try:
        import pymysql
    except ModuleNotFoundError as exc:
        raise RuntimeError("缺少 pymysql 依赖，请先安装: pip install pymysql") from exc

    mysql_config = build_mysql_config()
    conn = pymysql.connect(**mysql_config)

    try:
        existing = fetch_existing_news(conn)
        active_existing_ids = {
            biz_id for biz_id, status in existing.items() if status != delete_status
        }
        missing_on_site = sorted(active_existing_ids - source_biz_ids)

        print("\n========== 数据库比对结果 ==========")
        print(f"数据库同栏目官网新闻总数: {len(existing)}")
        print(f"数据库未逻辑删除新闻数: {len(active_existing_ids)}")
        print(f"官网全量新闻数: {len(source_biz_ids)}")
        print(f"待新增/更新新闻数: {len(parsed_news)}")
        print(f"待逻辑删除新闻数: {len(missing_on_site)}")

        if dry_run:
            print("当前为 dry-run 模式，不会写入或删除数据库数据")
            return

        upserted = upsert_news(conn, parsed_news, active_status)
        deleted = 0
        if no_delete:
            print("已指定 --no-delete，跳过逻辑删除")
        elif allow_delete:
            deleted = soft_delete_news(conn, missing_on_site, delete_status)
        else:
            print("本次不是完整全量抓取或官网列表为空，跳过逻辑删除以避免误删")

        conn.commit()
        print("\n========== 数据库同步完成 ==========")
        print(f"新增/更新成功: {upserted}")
        print(f"逻辑删除成功: {deleted}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="东方通官网新闻全量同步脚本")
    parser.add_argument("--max-pages", type=int, default=0, help="最多抓取多少页；0 表示不限制")
    parser.add_argument("--empty-page-limit", type=int, default=DEFAULT_EMPTY_PAGE_LIMIT, help="连续空页达到该数量后停止")
    parser.add_argument("--page-sleep", type=float, default=DEFAULT_PAGE_SLEEP, help="列表分页请求间隔秒数")
    parser.add_argument("--detail-sleep", type=float, default=DEFAULT_DETAIL_SLEEP, help="详情页请求间隔秒数")
    parser.add_argument("--detail-limit", type=int, default=0, help="最多解析多少条详情；0 表示不限制，调试用")
    parser.add_argument("--dry-run", action="store_true", help="只抓取和比对，不写入数据库")
    parser.add_argument("--crawl-only", action="store_true", help="只抓取官网数据，不连接数据库")
    parser.add_argument("--no-delete", action="store_true", help="只新增/更新，不对数据库缺失新闻做逻辑删除")
    parser.add_argument("--active-status", default=DEFAULT_ACTIVE_STATUS, help="正常数据 status 值")
    parser.add_argument("--delete-status", default=DEFAULT_DELETE_STATUS, help="逻辑删除 status 值")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    print("开始抓取东方通官网全量新闻...")
    news_list, completed = crawl_all_news(
        max_pages=args.max_pages,
        page_sleep=args.page_sleep,
        empty_page_limit=args.empty_page_limit,
    )

    if not news_list:
        print("官网新闻列表为空，终止任务以避免误删数据库数据")
        return 1

    source_biz_ids = {news["biz_id"] for news in news_list}
    print(f"\n官网新闻列表抓取完成，共 {len(news_list)} 条，完整抓取: {completed}")

    parsed_news, failed_news = parse_news_details(
        news_list=news_list,
        detail_sleep=args.detail_sleep,
        detail_limit=args.detail_limit,
    )
    print("\n========== 详情解析结果 ==========")
    print(f"解析成功: {len(parsed_news)}")
    print(f"解析失败: {len(failed_news)}")

    if args.crawl_only:
        print("已指定 --crawl-only，跳过数据库同步")
        return 0

    allow_delete = completed and args.detail_limit == 0 and len(source_biz_ids) > 0
    sync_database(
        source_biz_ids=source_biz_ids,
        parsed_news=parsed_news,
        dry_run=args.dry_run,
        no_delete=args.no_delete,
        allow_delete=allow_delete,
        active_status=args.active_status,
        delete_status=args.delete_status,
    )

    if failed_news:
        print("\n以下新闻详情解析失败，需要人工检查：")
        for news in failed_news:
            print(f"- {news['main_title']} {news['detail_url']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
