# -*- coding: utf-8 -*-
"""
从蓝皮书 PDF 中提取"济宁市2026年度标志性产业链紧缺专业人才需求目录"。
目标表(页43-92): 7列结构
  岗位名称 | 专业要求 | 紧缺星级 | 学历要求 | 任职能力要求 | 年薪均值(万元) | 工作经验年数要求
处理难点:
  1) 第1条数据常与子表头(星级/（万元）/要求)合并在同一单元格, 需按换行拆分
  2) 合并单元格导致部分行出现 None, 需要用上一行值向下填充
  3) 所属产业链来自页眉/章节标题, 需从页面文本提取
"""
import os
import re
import json
import pdfplumber

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "data", "bluebook_2026.pdf")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "bluebook_directory_raw.json")

# 15条标志性产业链名称(用于从页面文本中识别当前所属产业链)
CHAIN_KEYWORDS = [
    "工程机械", "专用装备", "汽车及零部件", "新能源汽车", "煤化工", "盐化工",
    "精细化工", "化工新材料", "新能源", "储能装备", "发电装备", "光伏",
    "新一代信息技术", "造纸和纸制品", "纺织服装", "轻工", "食品", "医药",
    "煤电", "装备"
]


def clean_cell(cell):
    """清理单元格: 去除换行/多余空白, None 转空串"""
    if cell is None:
        return ""
    s = str(cell).replace("\n", "").replace("\r", "").strip()
    return s


def split_subheader_and_value(cell):
    """
    处理形如 '星级\n5星' / '（万元）\n9.5' / '要求\n5' 的合并单元格。
    按首个换行拆分: 前半为子表头, 后半为真实值。
    返回 (sub_header, value)
    """
    if cell is None:
        return "", ""
    s = str(cell)
    if "\n" in s:
        parts = s.split("\n", 1)
        sub = parts[0].strip()
        val = parts[1].strip() if len(parts) > 1 else ""
        return sub, val
    return "", s.strip()


def parse_salary(cell):
    """从年薪单元格提取数值。如 '9.5' / '15' / '—' """
    s = clean_cell(cell)
    if not s or s in ("—", "-", "面议", "另议"):
        return None
    # 取首个数字
    m = re.search(r"\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def parse_exp_years(cell):
    """从工作经验单元格提取年数。如 '5' / '3' / '0' """
    s = clean_cell(cell)
    if not s or s in ("—", "-", "不限"):
        return None
    m = re.search(r"\d+", s)
    return int(m.group()) if m else None


def parse_star(cell):
    """提取紧缺星级。如 '5星' / '4星' / '—' """
    s = clean_cell(cell)
    if not s or s in ("—", "-"):
        return "—"
    m = re.search(r"(\d)\s*星", s)
    return f"{m.group(1)}星" if m else s


def detect_chain_from_text(text):
    """从页面文本中识别所属产业链名称。"""
    if not text:
        return None
    # 按出现顺序找首个匹配的关键词
    for kw in CHAIN_KEYWORDS:
        if kw in text:
            return kw
    return None


def extract_directory():
    print(f"解析需求目录: {PDF_PATH}")
    records = []
    chain_sequence = []  # 记录章节顺序

    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"总页数: {total}")

        current_chain = None
        # 目录从第43页开始(page index 42)
        for page_idx in range(42, total):
            page = pdf.pages[page_idx]
            page_no = page_idx + 1
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            # 章节标题识别: 页面顶部常含"XX产业链"或"XX装备"等
            # 取页面前 200 字符检测产业链
            head_text = page_text[:200]

            # 优先用页面首部出现的产业链名更新 current_chain
            detected = detect_chain_from_text(head_text)
            if detected:
                current_chain = detected

            # 提取该页所有表格
            try:
                tables = page.extract_tables()
            except Exception:
                tables = []

            for tbl in tables:
                if not tbl or len(tbl) < 2:
                    continue
                header = tbl[0]
                if not header or len(header) != 7:
                    continue
                # 确认是目标7列表: 表头应包含"岗位名称"
                header_str = "".join(clean_cell(c) for c in header)
                if "岗位名称" not in header_str:
                    continue

                # 第2行可能是 子表头+首条数据 的合并行
                # 逐行解析
                prev_row = None
                for ri, row in enumerate(tbl[1:], start=1):
                    if not row:
                        continue
                    # 跳过纯子表头行(如 ['数量（个）','占比',...]) - 这里7列表不会有
                    # 判断是否整行 None/空
                    non_empty = [c for c in row if c and str(c).strip()]
                    if not non_empty:
                        continue

                    # 拆分合并单元格
                    # 列0: 岗位名称 (可能含 ☆N 脚注标记, 需保留主名称)
                    # 列1: 专业要求
                    # 列2: 紧缺星级 (可能 '星级\n5星' 形式)
                    # 列3: 学历要求
                    # 列4: 任职能力要求
                    # 列5: 年薪均值 (可能 '（万元）\n9.5' 形式)
                    # 列6: 工作经验年数 (可能 '要求\n5' 形式)

                    job_raw = row[0]
                    major_raw = row[1]
                    star_raw = row[2]
                    edu_raw = row[3]
                    ability_raw = row[4]
                    salary_raw = row[5]
                    exp_raw = row[6]

                    # 处理星级/年薪/经验的子表头合并
                    _, star_val = split_subheader_and_value(star_raw)
                    _, salary_val = split_subheader_and_value(salary_raw)
                    _, exp_val = split_subheader_and_value(exp_raw)

                    # 岗位名称去脚注标记 ☆N
                    job_name = clean_cell(job_raw)
                    job_name = re.sub(r"☆\d*\s*$", "", job_name).strip()
                    job_name = re.sub(r"☆$", "", job_name).strip()

                    major = clean_cell(major_raw)
                    edu = clean_cell(edu_raw)
                    ability = clean_cell(ability_raw)

                    # 处理合并单元格的 None(向下填充)
                    # 若岗位名为空且其他字段也空, 跳过
                    if not job_name and not major and not star_val and not ability_raw:
                        continue

                    # 判断是否为续行: 岗位名为空 → 同一岗位的附加专业/学历
                    is_continuation = (not job_name) and prev_row is not None
                    if is_continuation:
                        # 续行: 继承父行所有空字段, 专业要求取本行新值
                        job_name = prev_row.get("岗位名称", "")
                        if not major:
                            major = prev_row.get("专业要求", "")
                        if not edu:
                            edu = prev_row.get("学历要求", "")
                        if not ability:
                            ability = prev_row.get("任职能力要求", "")
                        cur_star = parse_star(star_val) if star_val else prev_row.get("紧缺星级", "—")
                        cur_salary = parse_salary(salary_val) if salary_val else prev_row.get("年薪均值（万元）")
                        cur_exp = parse_exp_years(exp_val) if exp_val else prev_row.get("工作经验年数")
                    else:
                        cur_star = parse_star(star_val) if star_val else (
                            prev_row["紧缺星级"] if prev_row else "—"
                        )
                        cur_salary = parse_salary(salary_val) if salary_val else (
                            prev_row["年薪均值（万元）"] if prev_row else None
                        )
                        cur_exp = parse_exp_years(exp_val) if exp_val else (
                            prev_row["工作经验年数"] if prev_row else None
                        )

                    rec = {
                        "岗位名称": job_name,
                        "所属产业链": current_chain or "",
                        "紧缺星级": cur_star,
                        "学历要求": edu,
                        "专业要求": major,
                        "任职能力要求": ability,
                        "年薪均值（万元）": cur_salary,
                        "工作经验年数": cur_exp,
                        "页码": page_no,
                    }
                    records.append(rec)
                    prev_row = rec

            # 记录产业链顺序
            if current_chain and current_chain not in chain_sequence:
                chain_sequence.append(current_chain)

    print(f"\n提取记录数: {len(records)}")
    print(f"识别到产业链顺序: {chain_sequence}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "records": records,
            "chain_sequence": chain_sequence
        }, f, ensure_ascii=False, indent=2)
    print(f"已保存: {OUTPUT_PATH}")

    # 打印前5条样本
    print("\n前5条样本:")
    for r in records[:5]:
        print(json.dumps(r, ensure_ascii=False))
    return records


if __name__ == "__main__":
    extract_directory()
