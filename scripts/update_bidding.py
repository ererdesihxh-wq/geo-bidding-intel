#!/usr/bin/env python3
"""
GEO招投标情报更新工具
用法:
  python update_bidding.py                     # 查看当前数据总览
  python update_bidding.py --add               # 交互式添加新项目
  python update_bidding.py --batch "file.csv"  # 批量导入CSV
  python update_bidding.py --sync-docs         # 同步数据到docs/目录
"""
import json, os, csv, sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "bidding_data.json")
DOCS_DATA = os.path.join(BASE_DIR, "docs", "bidding_data.json")

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    data["meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    data["meta"]["total_projects"] = len(data["projects"])

    # Recalc status summary
    stats = {}
    industries = {}
    for p in data["projects"]:
        stats[p["status"]] = stats.get(p["status"], 0) + 1
        industries[p["industry"]] = industries.get(p["industry"], 0) + 1
    data["status_summary"] = stats
    data["industry_distribution"] = industries

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ 数据已保存: {DATA_FILE}")
    sync_docs(data)

def sync_docs(data=None):
    if data is None:
        data = load_data()
    with open(DOCS_DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ 已同步到docs: {DOCS_DATA}")

def add_project():
    """交互式添加新项目"""
    print("\n=== 添加新GEO招标项目 ===\n")
    p = {}
    p["id"] = f"GEO-{datetime.now().strftime('%Y')}-{datetime.now().strftime('%m%d')}-{os.urandom(2).hex()}"
    p["company"] = input("企业名称: ").strip()
    p["industry"] = input("所属行业: ").strip()
    p["title"] = input("项目标题: ").strip()

    print("状态选项: 招标中 / 已中标 / 已成交 / 情报收集")
    p["status"] = input("当前状态: ").strip()

    p["budget"] = input("预算金额: ").strip() or "未公开"
    p["bid_deadline"] = input("投标截止日期(YYYY-MM-DD): ").strip()
    p["publish_date"] = input("发布日期(YYYY-MM-DD): ").strip()
    p["summary"] = input("项目摘要: ").strip()
    p["winner"] = input("中标方(如有): ").strip()
    p["source_url"] = input("来源链接: ").strip()

    data = load_data()
    data["projects"].append(p)
    save_data(data)
    print(f"\n✓ 已添加: {p['company']} - {p['title']}")

def batch_import(csv_path):
    """从CSV批量导入"""
    if not os.path.exists(csv_path):
        print(f"✗ 文件不存在: {csv_path}")
        return
    data = load_data()
    count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = f"GEO-{datetime.now().strftime('%Y')}-{os.urandom(4).hex()}"
            data["projects"].append(row)
            count += 1
    save_data(data)
    print(f"✓ 批量导入: {count} 条")

def show_overview():
    data = load_data()
    print(f"\n{'='*50}")
    print(f"📊 GEO招投标情报站")
    print(f"{'='*50}")
    print(f"最后更新: {data['meta']['last_updated']}")
    print(f"项目总数: {data['meta']['total_projects']}")
    print(f"\n状态分布:")
    for s, c in sorted(data['status_summary'].items()):
        bar = '█' * c
        print(f"  {s}: {c} {bar}")
    print(f"\n行业分布:")
    for ind, c in sorted(data['industry_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {ind}: {c}")
    print(f"\n最近项目:")
    for p in sorted(data['projects'], key=lambda x: x.get('publish_date',''), reverse=True)[:5]:
        print(f"  [{p['status']}] {p['company']} - {p['title'][:40]}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_overview()
    elif sys.argv[1] == "--add":
        add_project()
    elif sys.argv[1] == "--batch" and len(sys.argv) > 2:
        batch_import(sys.argv[2])
    elif sys.argv[1] == "--sync-docs":
        sync_docs()
    elif sys.argv[1] == "--overview":
        show_overview()
    else:
        print("用法:")
        print("  python update_bidding.py                 概览")
        print("  python update_bidding.py --add           添加项目")
        print("  python update_bidding.py --batch file.csv 批量导入")
        print("  python update_bidding.py --sync-docs     同步到docs")
