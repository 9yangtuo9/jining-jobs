# -*- coding: utf-8 -*-
"""定位蓝皮书中包含岗位级字段(岗位/年薪/学历/专业/经验)的表格块。"""
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, "data", "bluebook_tables_raw.json")

with open(RAW_PATH, "r", encoding="utf-8") as f:
    blocks = json.load(f)

KEYWORDS = ["岗位", "年薪", "学历", "专业", "经验", "能力", "星级", "企业", "薪酬", "万元", "任职"]
print(f"扫描 {len(blocks)} 个表格块，查找含岗位级字段的表格...\n")

# 统计每个表格的列数分布
col_count_dist = {}
hit_blocks = []

for b in blocks:
    rows = b.get("rows", [])
    if not rows:
        continue
    header = rows[0]
    ncols = len(header) if header else 0
    col_count_dist[ncols] = col_count_dist.get(ncols, 0) + 1

    # 把表头+前2行数据拼成字符串做关键词匹配
    sample_text = ""
    for r in rows[:3]:
        if r:
            sample_text += " ".join([str(c) if c else "" for c in r]) + " "
    hits = [k for k in KEYWORDS if k in sample_text]
    if hits:
        hit_blocks.append((b, hits, ncols))

print("列数分布:")
for nc, cnt in sorted(col_count_dist.items()):
    print(f"  {nc} 列: {cnt} 个表格")

print(f"\n含目标关键词的表格块: {len(hit_blocks)} 个")
print("=" * 80)
for b, hits, ncols in hit_blocks[:40]:
    rows = b["rows"]
    print(f"\n[页 {b['page']} / 表 {b['table_index']}] 列数={ncols} 行数={len(rows)} 命中={hits}")
    print(f"  表头: {rows[0]}")
    if len(rows) > 1:
        print(f"  数据1: {rows[1]}")
    if len(rows) > 2:
        print(f"  数据2: {rows[2]}")
