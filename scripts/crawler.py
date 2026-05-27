#!/usr/bin/env python3
"""GEO招投标信息爬虫 - 自动发现新项目并更新数据"""
import json, os, sys, re, time, hashlib
from datetime import datetime
from urllib.parse import urlparse
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRAWLED_PATH = os.path.join(BASE_DIR, "data", "crawled_projects.json")

SEARCH_QUERIES = [
    "GEO优化 招标",
    "生成式引擎优化 招标",
    "GEO 招标 项目",
    "AI搜索优化 招标",
    "GEO优化 采购",
    "AI搜索引擎优化 招标",
    "GEO 投标 公告",
    "GEO 项目 招标公告",
]

GEO_KEYWORDS = [
    "GEO优化", "GEO ", "生成式引擎", "AI搜索优化", "AI搜索引擎",
    "生成式搜索引擎", "GEO项目", "GEO服务", "GEO采购",
    "生成式引擎优化", "AI搜索 优化",
]


def load_existing():
    """加载已有项目（curated + crawled）"""
    projects = []
    ids = set()

    # 1. 从 build_data.py 读 curated 项目
    data_path = os.path.join(BASE_DIR, "data", "bidding_data.json")
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for p in data.get("projects", []):
            projects.append(p)
            ids.add(p.get("source_url", ""))
            ids.add(p.get("id", ""))

    # 2. 读已爬取项目
    if os.path.exists(CRAWLED_PATH):
        with open(CRAWLED_PATH, "r", encoding="utf-8") as f:
            crawled = json.load(f)
        for p in crawled.get("projects", []):
            projects.append(p)
            ids.add(p.get("source_url", ""))
            ids.add(p.get("id", ""))

    return projects, ids


def is_duplicate(title, url, existing_projects, existing_ids):
    """去重检查 - URL匹配 + 多级标题模糊匹配"""
    if url and url in existing_ids:
        return True
    if not title:
        return False

    # 规范化：去空格、去标点、小写
    norm_title = re.sub(r'[\s\-—｜|()（）·,，。、]+', '', title).lower()[:40]

    for ep in existing_projects:
        etitle = ep.get("title", "")
        eurl = ep.get("source_url", "")
        if not etitle:
            continue

        # URL精确匹配
        if url and eurl and url == eurl:
            return True

        # 规范化标题
        enorm = re.sub(r'[\s\-—｜|()（）·,，。、]+', '', etitle).lower()[:40]

        # 1. 长度>10时一方包含另一方
        if len(norm_title) >= 10 and norm_title in enorm:
            return True
        if len(enorm) >= 10 and enorm in norm_title:
            return True

        # 2. 前15字符相等（去标点后）
        if norm_title[:15] and norm_title[:15] == enorm[:15]:
            return True

        # 3. 提取数字+年段匹配（如 "2026年" + "GEO"）
        year_match = re.search(r'(20\d{2})年', title)
        eyear_match = re.search(r'(20\d{2})年', etitle)
        if year_match and eyear_match and year_match.group(1) == eyear_match.group(1):
            # 同一年，检查是否有相同的核心词
            cores = ["GEO", "优化", "招标", "采购", "项目"]
            common_cores = sum(1 for c in cores if c in title and c in etitle)
            if common_cores >= 3:
                return True

    return False


def search_duckduckgo(query, max_results=8):
    """DuckDuckGo搜索（自动重试、限流保护）"""
    # 尝试多个可能的导入路径
    ddgs_module = None
    for mod_name in ["ddgs", "duckduckgo_search"]:
        try:
            ddgs_module = __import__(mod_name, fromlist=["DDGS"])
            break
        except ImportError:
            continue

    if ddgs_module is None:
        return None

    DDGS = ddgs_module.DDGS

    for attempt in range(3):
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
            time.sleep(2)
            return results
        except Exception as e:
            print(f"  DDG尝试 {attempt+1}/3 失败: {e}")
            time.sleep(3)
            continue
    return []


def search_bing(query, max_results=8):
    """Bing直接搜索（回退方案）"""
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/125.0.0.0 Safari/537.36"
        }
        url = f"https://www.bing.com/search?q={requests.utils.quote(query)}&count={max_results}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []

        results = []
        # 提取搜索结果 (Bing HTML结构)
        blocks = re.findall(
            r'<li class="b_algo">(.*?)</li>', resp.text, re.DOTALL
        )
        for block in blocks:
            link_m = re.search(r'href="(https?://[^"]+)"', block)
            title_m = re.search(r'<h2>.*?<a.*?>(.*?)</a>', block, re.DOTALL)
            snippet_m = re.search(r'<p class="b_lineclamp2">(.*?)</p>', block, re.DOTALL)
            if link_m:
                results.append({
                    "title": re.sub(r'<.*?>', '', title_m.group(1)) if title_m else "",
                    "url": link_m.group(1),
                    "snippet": re.sub(r'<.*?>', '', snippet_m.group(1)) if snippet_m else "",
                })
        time.sleep(1)
        return results
    except Exception as e:
        print(f"  Bing搜索失败: {e}")
        return []


def check_platforms_directly():
    """直接检查已知招标平台是否有GEO相关条目"""
    import requests
    platforms = [
        {
            "name": "千里马招标",
            "url": "https://gs.qianlima.com/search?keyword=GEO",
            "check": "GEO",
        },
        {
            "name": "招标投标公共服务平台",
            "url": "http://www.cebpubservice.com/search/?keyword=GEO",
            "check": "GEO",
        },
        {
            "name": "中国招标网",
            "url": "https://www.chinabidding.cn/search/search?searchkey=GEO",
            "check": "GEO",
        },
    ]
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/125.0.0.0 Safari/537.36"
    }
    for plat in platforms:
        try:
            resp = requests.get(plat["url"], headers=headers, timeout=15)
            if resp.status_code == 200:
                # 提取可能的结果链接
                links = re.findall(
                    r'<a[^>]*href="(https?://[^"]*?(?:bid|tender|zbgg|project)[^"]*)"[^>]*>'
                    r'(.*?)</a>', resp.text, re.DOTALL
                )
                for link_url, link_text in links[:5]:
                    text = re.sub(r'<.*?>', '', link_text).strip()
                    if text and any(kw.lower() in text.lower() for kw in GEO_KEYWORDS):
                        results.append({
                            "title": text,
                            "url": link_url if link_url.startswith("http") else "",
                            "snippet": f"来源: {plat['name']}",
                        })
            time.sleep(1)
        except Exception as e:
            print(f"  {plat['name']} 检查失败: {e}")
    return results


def extract_page_content(url):
    """访问页面并提取可读文本"""
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/125.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return ""

        text = resp.text
        # 提取正文文本（去掉HTML标签）
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:8000]  # 保留前8000字符
    except Exception as e:
        return ""


EXTRACT_PATTERNS = {
    "budget": [
        r'预算[：:]\s*([\d.]+)\s*万元',
        r'预算[：:]\s*([\d.]+)\s*万',
        r'采购预算[：:]\s*([\d.]+)\s*万元',
        r'最高限价[：:]\s*([\d.]+)\s*万元',
        r'控制价[：:]\s*([\d.]+)\s*万元',
        r'(\d+[\d,]*)\s*万元',
        r'保证金[：:]\s*([\d.]+)\s*万元',
        r'中标金额[：:]\s*([\d.]+)\s*万元',
    ],
    "deadline": [
        r'投标截止[：:时间]*\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2})',
        r'截止时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2})',
        r'提交投标文件截止[：:时间]*\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2})',
        r'开标时间[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2})',
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
    ],
    "company": [
        r'采购人[：:]\s*([^，。\r\n]{2,20})',
        r'招标人[：:]\s*([^，。\r\n]{2,20})',
        r'业主[：:]\s*([^，。\r\n]{2,20})',
        r'采购单位[：:]\s*([^，。\r\n]{2,20})',
        r'(?:受|由)\s*([^，。\r\n]{2,20})\s*委托',
    ],
    "winner": [
        r'中标[人商单位][：:]\s*([^，。\r\n]{2,30})',
        r'成交[人商单位][：:]\s*([^，。\r\n]{2,30})',
        r'第一中标候选人[：:]\s*([^，。\r\n]{2,30})',
        r'中标供应商[：:]\s*([^，。\r\n]{2,30})',
    ],
    "status_from_text": {
        "已中标": [r'中标公告', r'中标公示', r'成交公告', r'中标结果', r'已中标', r'结果公告'],
        "招标中": [r'招标公告', r'采购公告', r'招标中', r'正在招标', r'询价公告', r'竞争性磋商'],
        "已截止": [r'已截止', r'投标截止', r'已结束'],
        "已开标": [r'开标', r'已开标'],
    },
}


def extract_project(url, title, snippet):
    """从URL/标题/摘要中提取结构化项目信息"""
    project = {
        "id": "",
        "company": "",
        "industry": "",
        "title": title,
        "status": "待确认",
        "budget": "未公开",
        "bid_deadline": "",
        "publish_date": "",
        "summary": snippet,
        "winner": "",
        "source_url": url,
        "source": "crawled",
        "crawl_date": datetime.now().strftime("%Y-%m-%d"),
    }

    # 从页面内容中提取
    content = extract_page_content(url)
    if content:
        full_text = title + " " + snippet + " " + content
    else:
        full_text = title + " " + snippet

    # 提取预算
    for pat in EXTRACT_PATTERNS["budget"]:
        m = re.search(pat, full_text)
        if m:
            val = m.group(1).replace(",", "")
            try:
                project["budget"] = f"{float(val)}万元"
            except ValueError:
                project["budget"] = f"{val}万元"
            break

    # 提取投标截止日期
    for pat in EXTRACT_PATTERNS["deadline"]:
        m = re.search(pat, full_text)
        if m:
            if m.lastindex == 3:
                project["bid_deadline"] = f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
            else:
                d = m.group(1).replace("年", "-").replace("月", "-").replace("日", "")
                parts = d.split("-")
                if len(parts) == 3:
                    project["bid_deadline"] = f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
            break

    # 提取公司名
    for pat in EXTRACT_PATTERNS["company"]:
        m = re.search(pat, full_text)
        if m:
            project["company"] = m.group(1).strip()
            break

    # 提取中标方
    for pat in EXTRACT_PATTERNS["winner"]:
        m = re.search(pat, full_text)
        if m:
            project["winner"] = m.group(1).strip()
            break

    # 识别状态
    for status, patterns in EXTRACT_PATTERNS["status_from_text"].items():
        for p in patterns:
            if re.search(p, full_text):
                project["status"] = status
                break

    # 生成临时ID
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    project["id"] = f"CRAWL-{datetime.now().strftime('%Y%m%d')}-{url_hash}"

    return project


def is_geo_related(title, snippet):
    """判断是否与GEO招标相关 - 要求同时包含GEO关键词和招标/投标关键词"""
    combined = title + " " + snippet

    # 必须有中文内容（排除日文、英文无关结果）
    if not re.search(r'[一-鿿]', combined):
        return False

    has_geo = any(kw.lower() in combined.lower() for kw in GEO_KEYWORDS)
    if not has_geo:
        return False

    # 必须包含招标相关词（区分是招标项目而不是普通提及）
    bidding_kw = [
        "招标", "投标", "采购", "公告", "项目", "中标",
        "供应商", "询价", "竞争性磋商", "比选", "征集",
        "竞价", "招募", "招商", "标书", "投标截止",
        "投标人", "招标人", "采购人", "成交", "开标",
    ]
    has_bidding = any(kw in combined for kw in bidding_kw)
    if not has_bidding:
        return False

    # 排除明显是文章/博客/推荐类的内容（不是实际招标项目）
    article_kw = [
        "推荐", "公司推荐", "深度解析", "决策指南", "供应商有哪些",
        "成本直降", "新风口", "独立站", "最新", "专业顾问",
        "5大", "黄金标准", "评分", "评价", "哪家好",
    ]
    for kw in article_kw:
        if kw in title:
            return False

    return True


def load_crawled_history():
    """读取已保存的爬取历史"""
    if os.path.exists(CRAWLED_PATH):
        with open(CRAWLED_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"projects": [], "crawl_history": []}


def save_crawled_history(data):
    """保存爬取历史"""
    os.makedirs(os.path.dirname(CRAWLED_PATH), exist_ok=True)
    with open(CRAWLED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print(f"{'='*60}")
    print(f"  GEO招投标爬虫  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    # 加载已有项目
    existing_projects, existing_ids = load_existing()
    print(f"\n已有项目: {len(existing_projects)} 个 (含爬取)")

    # 加载爬取历史
    history = load_crawled_history()
    crawled_list = history.get("projects", [])

    # 收集爬取URL去重
    crawled_urls_hist = {p.get("source_url", "") for p in crawled_list if p.get("source_url")}

    all_new = []
    seen_urls = set()
    seen_titles_norm = set()  # 同一轮内已接受项目的规范化标题

    # === 1. DuckDuckGo 搜索 ===
    print("\n[1/3] DuckDuckGo 搜索...")
    for i, query in enumerate(SEARCH_QUERIES):
        if i > 0:
            time.sleep(3)  # 查询间隔，避免限流
        results = search_duckduckgo(query)
        if results is None:
            print("  DDGS不可用，切换到Bing搜索")
            break
        for r in results:
            url = r.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            if not is_geo_related(r.get("title", ""), r.get("snippet", "")):
                continue
            if is_duplicate(r.get("title", ""), url, existing_projects, existing_ids | crawled_urls_hist):
                continue
            # 同轮次去重
            r_norm = re.sub(r'[\s\-—｜|()（）·,，。、]+', '', r.get("title", "")).lower()[:30]
            if r_norm in seen_titles_norm:
                continue
            seen_titles_norm.add(r_norm)
            all_new.append(r)
        print(f"  [{query[:20]:20s}] {len(results):2d} 结果 | 新增 {sum(1 for x in results if x.get('url','') not in seen_urls)}")

    # === 2. Bing 搜索（如果DDG不可用） ===
    if all_new is None or (not all_new and len(seen_urls) < 5):
        print("\n[2/3] Bing搜索...")
        for query in SEARCH_QUERIES:
            results = search_bing(query)
            for r in results:
                url = r.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                if not is_geo_related(r.get("title", ""), r.get("snippet", "")):
                    continue
                if is_duplicate(r.get("title", ""), url, existing_projects, existing_ids | crawled_urls_hist):
                    continue
                r_norm = re.sub(r'[\s\-—｜|()（）·,，。、]+', '', r.get("title", "")).lower()[:30]
                if r_norm in seen_titles_norm:
                    continue
                seen_titles_norm.add(r_norm)
                all_new.append(r)

    # === 3. 直接检查招标平台 ===
    print("\n[3/3] 直接检查招标平台...")
    platform_results = check_platforms_directly()
    for r in platform_results:
        url = r.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        if is_duplicate(r.get("title", ""), url, existing_projects, existing_ids | crawled_urls_hist):
            continue
        r_norm = re.sub(r'[\s\-—｜|()（）·,，。、]+', '', r.get("title", "")).lower()[:30]
        if r_norm in seen_titles_norm:
            continue
        seen_titles_norm.add(r_norm)
        all_new.append(r)

    # === 处理新发现项目 ===
    print(f"\n{'='*60}")
    print(f"  发现 {len(all_new)} 个候选项目")
    print(f"{'='*60}")

    added = 0
    for item in all_new:
        project = extract_project(item["url"], item["title"], item["snippet"])
        crawled_list.append(project)
        added += 1
        print(f"\n  [{added}] {project['title'][:60]}")
        print(f"       公司: {project['company'] or '待识别'}")
        print(f"       预算: {project['budget']}")
        print(f"       截止: {project['bid_deadline'] or '待识别'}")
        print(f"       状态: {project['status']}")
        print(f"       URL: {project['source_url'][:70]}")

    # 保存
    history["projects"] = crawled_list
    history["crawl_history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "new_found": added,
        "total_searched": len(seen_urls),
    })
    save_crawled_history(history)

    print(f"\n{'='*60}")
    print(f"  爬取完成")
    print(f"  总计爬取项目: {len(crawled_list)} 个")
    print(f"  本次新增: {added} 个")
    print(f"  历史运行: {len(history['crawl_history'])} 次")
    print(f"  数据保存: {CRAWLED_PATH}")
    print(f"{'='*60}")

    return added


if __name__ == "__main__":
    main()
