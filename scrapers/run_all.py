# -*- coding: utf-8 -*-
"""
济宁岗位数据采集 - 主控脚本
一键复现全部数据源采集 → 统一清洗 → jobs.json

依赖: pip install pdfplumber requests beautifulsoup4
运行: python scrapers/run_all.py
"""
import os
import sys
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable

# 采集流程(顺序执行)
STEPS = [
    ("1/7 蓝皮书下载与表格预解析", "fetch_bluebook_pdf.py"),
    ("2/7 蓝皮书紧缺岗位目录提取(730条)", "extract_directory.py"),
    ("3/7 人社局事业单位岗位PDF采集", "fetch_hrss_pdf.py"),
    ("4/7 汶上县招聘公告采集", "fetch_wenshang_notices.py"),
    ("5/7 济宁直聘网首页岗位采集", "fetch_jiningzhipin.py"),
    ("6/7 济宁直聘网详情页字段补充", "enrich_jzp_details.py"),
    ("7/7 统一清洗 → jobs.json", "build_jobs_json.py"),
]


def run(script):
    path = os.path.join(HERE, script)
    print(f"\n>>> 运行 {script}")
    print("-" * 60)
    t0 = time.time()
    r = subprocess.run([PY, path], cwd=ROOT)
    dt = time.time() - t0
    print("-" * 60)
    print(f"<<< {script} 完成 (耗时 {dt:.1f}s, 退出码 {r.returncode})")
    return r.returncode == 0


def main():
    print("=" * 60)
    print("济宁热门工作岗位数据采集 - 全流程")
    print("=" * 60)
    print(f"项目根目录: {ROOT}")
    print(f"Python: {PY}\n")

    t0 = time.time()
    results = []
    for desc, script in STEPS:
        print(f"\n【{desc}】")
        ok = run(script)
        results.append((script, ok))
        if not ok:
            print(f"  ⚠️ {script} 执行失败, 继续后续步骤...")

    print("\n" + "=" * 60)
    print("全流程汇总")
    print("=" * 60)
    for script, ok in results:
        print(f"  {'✅' if ok else '❌'} {script}")
    print(f"\n总耗时: {time.time()-t0:.1f}s")
    jobs_path = os.path.join(ROOT, "jobs.json")
    if os.path.exists(jobs_path):
        import json
        with open(jobs_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        print(f"✅ jobs.json 已生成: {jobs_path}")
        print(f"   总记录数: {d.get('total')}")
        print(f"   采集日期: {d.get('data_acquisition_date')}")
        print(f"   数据源分布: {d.get('summary', {}).get('by_source')}")
    else:
        print("❌ jobs.json 未生成, 请检查上述失败步骤")


if __name__ == "__main__":
    main()
