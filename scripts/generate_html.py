#!/usr/bin/env python3
"""从bidding_data.json生成docs/index.html（内嵌数据版本，本地可直接打开）"""
import json, os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "bidding_data.json")
HTML_FILE = os.path.join(BASE_DIR, "docs", "index.html")

with open(DATA_FILE, "r", encoding="utf-8") as f:
  data = json.load(f)

# Read existing HTML template
with open(HTML_FILE, "r", encoding="utf-8") as f:
  html = f.read()

# Replace INLINE_DATA
json_str = json.dumps(data, ensure_ascii=False)
new_html = re.sub(
  r'var INLINE_DATA = .*?;\n',
  f'var INLINE_DATA = {json_str};\n',
  html,
  flags=re.DOTALL
)

with open(HTML_FILE, "w", encoding="utf-8") as f:
  f.write(new_html)
print(f"HTML updated: {HTML_FILE}")
print(f"Embedded {len(data['projects'])} projects inline")
