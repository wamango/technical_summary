# -*- coding: utf-8 -*-
"""
tongtech.com 新闻抓取脚本
简化版：只抓取第一页中昨天发布的新闻
"""

import hashlib
import pymysql
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin
import time

# ====================== 配置 ======================
MYSQL_CONFIG = {
    "host": "10.10.80.52",
    "port": 3306,
    "user": "root",
    "password": "Golden!@#dftoms",
    "database": "tongframework_dev",
    "charset": "utf8mb4"
}

CREATE_BY = "1242684364872761344"
SECTION_ID = "26e1ac838e2241e6aec69d79fcaa745a"
CONTEXT_PUBLISHED = "1"
CONTEXT_AUTHOR = "超级管理员"
ENCLOSURE = "[]"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

BASE_URL = "https://www.tongtech.com"
START_URL = f"{BASE_URL}/news/1.html"
# ===================================================

def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def get_soup(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"请求失败: {url}, 错误: {e}")
        return None

def get_yesterday_date():
    """获取昨天的日期，格式为 YYYY-MM-DD"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def normalize_rich_text(html_content):
    if not html_content:
        return "<div></div>"
        
    soup = BeautifulSoup(html_content, "lxml")
    
    # 如果传入的是完整的div.neirongxq，直接使用
    neirongxq = soup.find("div", class_="neirongxq")
    if not neirongxq:
        # 如果没有找到，尝试使用传入的html_content本身
        neirongxq = soup
    
    # 1. 标准化所有 <p>
    for p in neirongxq.find_all("p"):
        style = p.get("style", "")
        base_style = (
            "box-sizing: border-box; margin: 0px; padding: 0px; font-size: 16px; "
            "white-space: normal; color: #222222; line-height: 1.75;"
        )
        if "text-align:justify" in style or "background-color:#FFFFFF" in style:
            base_style += " text-align:justify; background-color:#FFFFFF;"
        p["style"] = base_style

        # 关键：如果是空行，保留 &nbsp; 但添加 class 隐藏
        if p.get_text(strip=True) == "":
            p.clear()
            p.append(BeautifulSoup("&nbsp;", "html.parser"))
            p["class"] = p.get("class", []) + ["empty-line"]

    # 2. 图片处理
    for img in neirongxq.find_all("img"):
        img["class"] = img.get("class", []) + ["syl-page-img"]
        img["style"] = (
            "box-sizing: border-box; border: 0; vertical-align: middle; "
            "display: block; margin: 15px auto; max-width: 80%; height: auto;"
        )
        # 确保图片链接是完整的URL
        if img.get("src") and not img["src"].startswith(('http://', 'https://')):
            img["src"] = urljoin(BASE_URL, img["src"])

    for div in neirongxq.find_all("div", class_="pgc-img"):
        div["style"] = (
            "box-sizing: border-box; margin: 18px 0; padding: 0; font-size: 16px; "
            "text-align: center; color: #222222;"
        )

    # 3. 清理不必要的 <br>（保留必要的换行）
    for br in neirongxq.find_all("br"):
        # 如果br在空p标签中，删除br
        parent = br.parent
        if parent and parent.name == "p" and len(parent.contents) == 1:
            br.decompose()

    # 4. 注入 CSS：隐藏 &nbsp; 字符（但保留高度）
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

def get_news_list():
    """获取第一页的新闻列表"""
    soup = get_soup(START_URL)
    if not soup:
        return []
    
    items = soup.select(".gywm_news ul li")
    news_list = []
    
    for item in items:
        title_span = item.select_one(".biaoti2")
        main_title = title_span.get_text(strip=True) if title_span else ""
        main_title = re.sub(r"\s+", " ", main_title).strip()

        sub_div = item.select_one(".wenzix")
        sub_title = sub_div.get_text(strip=True) if sub_div else ""

        more_a = item.select_one(".chakangengduo a")
        detail_url = urljoin(BASE_URL, more_a["href"]) if more_a and more_a.get("href") else ""

        date_span = item.select_one(".shijian2")
        pub_date = date_span.get_text(strip=True) if date_span else ""
        
        # 提取日期，用于判断是否为昨天
        date_match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', pub_date)
        if date_match:
            news_date = date_match.group(1)
        else:
            news_date = ""
        
        if main_title and detail_url:
            news_list.append({
                "main_title": main_title,
                "sub_title": sub_title,
                "detail_url": detail_url,
                "pub_date": pub_date,
                "news_date": news_date
            })
    
    return news_list

def parse_detail(detail_url, list_pub_date):
    soup = get_soup(detail_url)
    if not soup:
        return None
    
    # 改进的内容提取方法
    content_html = ""
    
    # 方法1：直接查找neirongxq
    raw_content = soup.select_one(".neirongxq")
    
    # 方法2：如果方法1找不到，尝试其他可能的选择器
    if not raw_content:
        # 尝试其他可能的内容容器
        possible_selectors = [
            ".news-content",
            ".content",
            ".article-content",
            ".detail-content",
            ".main-content"
        ]
        for selector in possible_selectors:
            raw_content = soup.select_one(selector)
            if raw_content:
                break
    
    # 方法3：如果还是找不到，尝试查找包含大量文本的div
    if not raw_content:
        # 查找包含多个p标签或大量文本的div
        all_divs = soup.find_all("div")
        for div in all_divs:
            text_length = len(div.get_text(strip=True))
            p_count = len(div.find_all("p"))
            if text_length > 200 or p_count > 2:
                raw_content = div
                break
    
    if raw_content:
        content_html = normalize_rich_text(str(raw_content))
    else:
        content_html = "<div></div>"

    # 发布时间
    pub_time_str = list_pub_date
    detail_time_p = soup.select_one(".xinwenxiangqing_bt p")
    if detail_time_p:
        pub_time_str = detail_time_p.get_text(strip=True)

    pub_time = "1970-01-01 00:00:00"
    if pub_time_str:
        # 改进日期提取，支持更多格式
        date_patterns = [
            r"(\d{4}[-年]\d{1,2}[-月]\d{1,2})",
            r"(\d{4}/\d{1,2}/\d{1,2})",
            r"(\d{4}\.\d{1,2}\.\d{1,2})"
        ]
        for pattern in date_patterns:
            m = re.search(pattern, pub_time_str)
            if m:
                date_clean = m.group(1).replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(".", "-")
                try:
                    pub_time = datetime.strptime(date_clean, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
                    break
                except:
                    continue

    # 关键词和来源
    kw = soup.select_one('meta[name="keywords"]')
    keywords = kw["content"] if kw and kw.get("content") else ""

    source = "东方通官网"

    # 提取第一张图片作为封面
    img_soup = BeautifulSoup(content_html, "lxml")
    img = img_soup.select_one("img")
    pic_link = ""
    if img and img.get("src"):
        pic_link = urljoin(detail_url, img["src"])

    return {
        "published_time": pub_time,
        "content": content_html,
        "summary": "",
        "keywords": keywords,
        "source": source,
        "pic_link": pic_link,
        "origin_url": detail_url
    }

def save_to_db(main_title, sub_title, detail_data):
    conn = pymysql.connect(**MYSQL_CONFIG)
    cur = conn.cursor()

    biz_id = md5(detail_data["origin_url"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = """
    INSERT INTO `t_portal_context`(
        `biz_id`, `status`, `create_by`, `create_date`, `update_by`, `update_date`,
        `remarks`, `section_id`, `context_title`, `context_sub_title`,
        `context_keywords`, `context_source`, `context_summary`, `context_main`,
        `published_time`, `context_re_link`, `context_pic_link`, `context_published`,
        `context_author`, `context_author_id`, `enclosure`
    ) VALUES (
        %s, '0', %s, %s, %s, %s, NULL, %s, %s, %s,
        %s, %s, %s, %s, %s, '', %s, %s, %s, %s, %s
    )
    ON DUPLICATE KEY UPDATE
        update_by=VALUES(update_by), update_date=VALUES(update_date),
        context_title=VALUES(context_title), context_sub_title=VALUES(context_sub_title),
        context_main=VALUES(context_main), context_summary=VALUES(context_summary),
        context_pic_link=VALUES(context_pic_link);
    """

    params = (
        biz_id, CREATE_BY, now, CREATE_BY, now,
        SECTION_ID, main_title, sub_title,
        detail_data["keywords"], detail_data["source"], detail_data["summary"], detail_data["content"],
        detail_data["published_time"], detail_data["pic_link"],
        CONTEXT_PUBLISHED, CONTEXT_AUTHOR, CREATE_BY, ENCLOSURE
    )

    try:
        cur.execute(sql, params)
        conn.commit()
        print(f"入库成功: {main_title}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"入库失败: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def crawl_yesterday_news():
    """抓取昨天发布的所有新闻"""
    yesterday = get_yesterday_date()
    print(f"开始抓取 {yesterday} 的新闻...")
    
    # 获取第一页新闻列表
    print(f"正在抓取新闻列表页: {START_URL}")
    news_list = get_news_list()
    
    if not news_list:
        print("未找到任何新闻")
        return
    
    print(f"第一页共找到 {len(news_list)} 条新闻")
    
    # 筛选昨天的新闻
    yesterday_news = [news for news in news_list if news["news_date"] == yesterday]
    
    if not yesterday_news:
        print(f"第一页中没有找到 {yesterday} 发布的新闻")
        return
    
    print(f"找到 {len(yesterday_news)} 条昨天发布的新闻")
    
    # 处理每条新闻
    success_count = 0
    for news in yesterday_news:
        print(f"\n处理新闻: {news['main_title']}")
        print(f"发布日期: {news['news_date']}")
        print(f"详情页: {news['detail_url']}")
        
        detail_data = parse_detail(news["detail_url"], news["pub_date"])
        if detail_data:
            if save_to_db(news["main_title"], news["sub_title"], detail_data):
                success_count += 1
            
            # 避免请求过快
            time.sleep(1)
        else:
            print(f"解析详情页失败: {news['detail_url']}")
    
    print(f"\n任务完成！成功处理 {success_count}/{len(yesterday_news)} 条昨天新闻")

# ====================== 主程序 ======================
if __name__ == "__main__":
    crawl_yesterday_news()