#!/usr/bin/env python3
"""
GEO 招投标情报分析工具 (CLI)
用法:
  python analyze_bidding.py --text "招标公告内容..."
  python analyze_bidding.py --url "https://example.com/bidding/123"
  python analyze_bidding.py --interactive
  python analyze_bidding.py --help
"""
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# ===== 关键词评分表 =====
GEO_KEYWORDS = {
    "deepseek": 15, "豆包": 15, "文心一言": 15, "通义千问": 15,
    "kimi": 15, "元宝": 10, "ai平台": 10, "多平台": 8,
    "年框": 8, "kpi": 5, "语义匹配": 10, "合规": 5,
    "露出率": 10, "监测": 5, "chatgpt": 10, "gemini": 10,
    "ai搜索": 12, "ai优化": 12, "大模型": 10, "词条": 5,
}


def extract_client(text):
    patterns = [
        rf"招标[人方][：:]\s*([^\s，,。\n\r]+)",
        rf"采购[人方][：:]\s*([^\s，,。\n\r]+)",
        rf"业主[：:]\s*([^\s，,。\n\r]+)",
        rf"甲方[：:]\s*([^\s，,。\n\r]+)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return ""


def extract_budget(text):
    m = re.search(r"([\d.]+)\s*万元", text)
    if m:
        return m.group(0)
    m = re.search(r"预算[：:]\s*([^\s，,。\n\r]+)", text)
    if m:
        return m.group(1)
    return ""


def extract_deadline(text):
    m = re.search(r"截止[^：:]*[：:]?\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2})", text)
    if m:
        return m.group(1).replace("年", "-").replace("月", "-")
    return ""


def extract_title(text):
    m = re.search(r"项目名[称][：:]\s*([^\n\r]+)", text)
    if m:
        return m.group(1).strip()
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if "项目" in line and len(line) < 60:
            return line
    return ""


def compute_geo_relevance(text):
    lower = text.lower()
    score = 0
    for kw, pts in GEO_KEYWORDS.items():
        if kw in lower:
            score += pts
    tier = "高" if score >= 50 else ("中" if score >= 20 else "低")
    return {"score": min(score, 100), "tier": tier}


def compute_priority(budget_str):
    m = re.search(r"([\d.]+)", budget_str)
    if m:
        val = float(m.group(1))
        if val >= 100:
            return "P0"
        if val >= 30:
            return "P1"
    return "P2"


def detect_signals(text):
    signals = []
    if "政府" in text:
        signals.append("🏛 政府采购")
    if "金融" in text:
        signals.append("🏦 金融行业")
    if "年框" in text:
        signals.append("📅 年框制")
    if "国际" in text or "海外" in text or "gemini" in text.lower():
        signals.append("🌐 国际GEO")
    if "智能体" in text or "智能获客" in text:
        signals.append("🤖 AI智能体")
    return signals


def analyze_text(text):
    """输入招标文本，输出结构化分析结果"""
    client = extract_client(text)
    budget = extract_budget(text)
    deadline = extract_deadline(text)
    title = extract_title(text)
    geo = compute_geo_relevance(text)
    priority = compute_priority(budget)
    signals = detect_signals(text)

    return {
        "甲方_采购方": client or "待确认",
        "项目名称": title or "待确认",
        "预算_金额": budget or "未公开",
        "投标截止日期": deadline or "未知",
        "GEO相关度": {"等级": geo["tier"], "分数": geo["score"]},
        "优先级": priority,
        "趋势信号": signals,
        "原始文本摘要": text[:200] + "..." if len(text) > 200 else text,
    }


def format_output(result, fmt="text"):
    if fmt == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)

    lines = []
    lines.append("=" * 50)
    lines.append("  GEO 情报分析报告")
    lines.append("=" * 50)
    lines.append(f"  甲方/采购方:  {result['甲方_采购方']}")
    lines.append(f"  项目名称:    {result['项目名称']}")
    lines.append(f"  预算/金额:    {result['预算_金额']}")
    lines.append(f"  投标截止:    {result['投标截止日期']}")
    lines.append(f"  GEO相关度:   {result['GEO相关度']['等级']} ({result['GEO相关度']['分数']}分)")
    lines.append(f"  优先级:      {result['优先级']}")
    signals = result.get("趋势信号", [])
    if signals:
        lines.append(f"  趋势信号:    {'  '.join(signals)}")
    else:
        lines.append(f"  趋势信号:    无")
    lines.append("-" * 50)
    lines.append(f"  原始文本:")
    lines.append(f"  {result['原始文本摘要']}")
    lines.append("=" * 50)
    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="GEO 招投标情报分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python analyze_bidding.py --text "项目名称：XX项目 招标人：XX公司 预算：100万元"
  python analyze_bidding.py --text "..." --json
  python analyze_bidding.py --interactive
        """,
    )
    parser.add_argument("--text", type=str, help="招标公告文本")
    parser.add_argument("--url", type=str, help="招标公告URL (需安装requests)")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式输入")

    args = parser.parse_args()

    if args.interactive:
        print("请输入招标公告文本 (Ctrl+D 或 Ctrl+Z 结束):")
        text = sys.stdin.read().strip()
        if not text:
            print("未输入任何内容")
            return
        result = analyze_text(text)
        print()
        print(format_output(result, "json" if args.json else "text"))
        return

    if args.url:
        try:
            import requests
        except ImportError:
            print("错误: 使用 --url 需要安装 requests: pip install requests")
            print("提示: 可以先复制文本内容，用 --text 参数传入")
            sys.exit(1)
        try:
            resp = requests.get(args.url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp.encoding = "utf-8"
            text = resp.text
        except Exception as e:
            print(f"错误: 无法获取URL内容: {e}")
            sys.exit(1)

    elif args.text:
        text = args.text
    else:
        parser.print_help()
        return

    result = analyze_text(text)
    print(format_output(result, "json" if args.json else "text"))


if __name__ == "__main__":
    main()
