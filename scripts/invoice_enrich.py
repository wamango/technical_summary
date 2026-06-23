#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票 Excel 回填：查 t_biz_invoice，把流程标题/流程条形码/流程申请人名称写回表格。

用法（把本脚本和 2023年取得发票.xlsx 放同一目录）:
  pip install pandas openpyxl pymysql
  python invoice_enrich.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import pymysql

# ========== 数据库连接（已写死，直接改这里即可）==========
DB_HOST = "10.10.80.52"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "Golden!@#dftoms"
DB_NAME = "tongframework_dev"
DB_TABLE = "t_biz_invoice"

# Excel：与脚本同目录下的文件名
SCRIPT_DIR = Path(__file__).resolve().parent
EXCEL_FILE = SCRIPT_DIR / "2023年取得发票.xlsx"
OUTPUT_FILE = SCRIPT_DIR / "2023年取得发票_已匹配.xlsx"
EXCEL_SHEET = "Sheet1"
BATCH_SIZE = 400

# 表字段名（留空则自动从表里识别）
FIELD_INVOICE_CODE = ""
FIELD_INVOICE_NO = ""
FIELD_FLOW_TITLE = ""
FIELD_FLOW_BARCODE = ""
FIELD_APPLY_USER_NAME = ""
# =====================================================

OUT_COL_TITLE = "流程标题"
OUT_COL_BARCODE = "流程条形码"
OUT_COL_APPLICANT = "流程申请人名称"

FIELD_CANDIDATES = {
    "invoice_code": ["invoice_code", "fpdm", "fapiao_code", "发票代码"],
    "invoice_no": ["invoice_no", "invoice_number", "invoice_num", "fphm", "发票号码"],
    "flow_title": ["flow_title", "process_title", "workflow_title", "流程标题"],
    "flow_barcode": ["flow_barcode", "process_barcode", "bar_code", "barcode", "流程条形码"],
    "apply_user_name": [
        "apply_user_name",
        "applicant_name",
        "process_apply_user_name",
        "流程申请人名称",
        "申请人名称",
    ],
}


def normalize_str(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if text in ("--", "nan", "None", "NaT"):
        return ""
    if re.fullmatch(r"\d+\.0", text):
        return text[:-2]
    return text


def connect_mysql() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def list_table_columns(conn: pymysql.connections.Connection) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(f"SHOW COLUMNS FROM `{DB_TABLE}`")
        return [row["Field"] for row in cur.fetchall()]


def pick_column(columns: Sequence[str], logical: str, hardcoded: str) -> Optional[str]:
    if hardcoded:
        if hardcoded not in columns:
            raise RuntimeError(f"字段 {hardcoded} 不在表 {DB_TABLE} 中，可用列: {columns}")
        return hardcoded
    lower_map = {c.lower(): c for c in columns}
    for name in FIELD_CANDIDATES[logical]:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
        if name in columns:
            return name
    return None


def resolve_fields(conn: pymysql.connections.Connection) -> Dict[str, str]:
    columns = list_table_columns(conn)
    hardcoded = {
        "invoice_code": FIELD_INVOICE_CODE,
        "invoice_no": FIELD_INVOICE_NO,
        "flow_title": FIELD_FLOW_TITLE,
        "flow_barcode": FIELD_FLOW_BARCODE,
        "apply_user_name": FIELD_APPLY_USER_NAME,
    }
    resolved: Dict[str, str] = {}
    missing: List[str] = []
    for logical in FIELD_CANDIDATES:
        col = pick_column(columns, logical, hardcoded[logical])
        if col:
            resolved[logical] = col
        else:
            missing.append(logical)
    if missing:
        print("无法自动识别以下字段，请改脚本顶部的 FIELD_* 常量:")
        for name in missing:
            print(f"  - {name}")
        print(f"\n表 {DB_TABLE} 全部列名:")
        for col in columns:
            print(f"  {col}")
        sys.exit(1)
    print("字段映射:")
    for k, v in resolved.items():
        print(f"  {k} -> {v}")
    return resolved


def chunked(items: Sequence[Any], size: int) -> List[List[Any]]:
    return [list(items[i : i + size]) for i in range(0, len(items), size)]


def fetch_db_records(
    conn: pymysql.connections.Connection,
    fields: Dict[str, str],
    pairs: Sequence[Tuple[str, str]],
    numbers_only: Sequence[str],
) -> Tuple[Dict[Tuple[str, str], Dict[str, str]], Dict[str, Dict[str, str]]]:
    code_col = fields["invoice_code"]
    no_col = fields["invoice_no"]
    title_col = fields["flow_title"]
    barcode_col = fields["flow_barcode"]
    applicant_col = fields["apply_user_name"]

    pair_map: Dict[Tuple[str, str], Dict[str, str]] = {}
    no_map: Dict[str, Dict[str, str]] = {}

    def absorb(row: Dict[str, Any]) -> None:
        code = normalize_str(row.get("invoice_code"))
        no = normalize_str(row.get("invoice_no"))
        payload = {
            OUT_COL_TITLE: normalize_str(row.get("flow_title")),
            OUT_COL_BARCODE: normalize_str(row.get("flow_barcode")),
            OUT_COL_APPLICANT: normalize_str(row.get("apply_user_name")),
        }
        if code and no:
            pair_map.setdefault((code, no), payload)
        if no:
            no_map.setdefault(no, payload)

    select_sql = (
        f"SELECT `{code_col}` AS invoice_code, `{no_col}` AS invoice_no, "
        f"`{title_col}` AS flow_title, `{barcode_col}` AS flow_barcode, "
        f"`{applicant_col}` AS apply_user_name FROM `{DB_TABLE}`"
    )

    with conn.cursor() as cur:
        for batch in chunked(list(pairs), BATCH_SIZE):
            placeholders = ",".join(["(%s,%s)"] * len(batch))
            params: List[str] = []
            for code, no in batch:
                params.extend([code, no])
            sql = f"{select_sql} WHERE (`{code_col}`, `{no_col}`) IN ({placeholders})"
            cur.execute(sql, params)
            for row in cur.fetchall():
                absorb(row)

        for batch in chunked(sorted(set(numbers_only)), BATCH_SIZE):
            placeholders = ",".join(["%s"] * len(batch))
            sql = f"{select_sql} WHERE `{no_col}` IN ({placeholders})"
            cur.execute(sql, batch)
            for row in cur.fetchall():
                absorb(row)

    return pair_map, no_map


def lookup_row(
    code: str,
    no: str,
    digital: str,
    pair_map: Dict[Tuple[str, str], Dict[str, str]],
    no_map: Dict[str, Dict[str, str]],
) -> Dict[str, str]:
    empty = {OUT_COL_TITLE: "", OUT_COL_BARCODE: "", OUT_COL_APPLICANT: ""}
    if code and no:
        hit = pair_map.get((code, no))
        if hit:
            return hit
    if digital:
        hit = no_map.get(digital)
        if hit:
            return hit
    if no and not code:
        hit = no_map.get(no)
        if hit:
            return hit
    return empty


def main() -> None:
    if not EXCEL_FILE.exists():
        print(f"找不到 Excel: {EXCEL_FILE}")
        print("请把 2023年取得发票.xlsx 放在脚本同目录下再执行。")
        sys.exit(1)

    print(f"连接数据库 {DB_HOST}:{DB_PORT} / {DB_NAME} ...")
    conn = connect_mysql()
    try:
        fields = resolve_fields(conn)

        print(f"读取 Excel: {EXCEL_FILE} [{EXCEL_SHEET}]")
        df = pd.read_excel(EXCEL_FILE, sheet_name=EXCEL_SHEET, header=0, dtype=object)

        pairs: List[Tuple[str, str]] = []
        numbers_only: List[str] = []
        for _, row in df.iterrows():
            code = normalize_str(row.get("发票代码"))
            no = normalize_str(row.get("发票号码"))
            digital = normalize_str(row.get("数电发票号码"))
            if code and no:
                pairs.append((code, no))
            elif digital:
                numbers_only.append(digital)

        pairs = list(dict.fromkeys(pairs))
        numbers_only = list(dict.fromkeys(numbers_only))
        print(f"待查询: 代码+号码 {len(pairs)} 组, 仅号码 {len(numbers_only)} 个")

        pair_map, no_map = fetch_db_records(conn, fields, pairs, numbers_only)
        print(f"数据库命中: 代码+号码 {len(pair_map)} 组, 仅号码 {len(no_map)} 个")

        titles, barcodes, applicants = [], [], []
        matched = 0
        for _, row in df.iterrows():
            code = normalize_str(row.get("发票代码"))
            no = normalize_str(row.get("发票号码"))
            digital = normalize_str(row.get("数电发票号码"))
            hit = lookup_row(code, no, digital, pair_map, no_map)
            titles.append(hit[OUT_COL_TITLE])
            barcodes.append(hit[OUT_COL_BARCODE])
            applicants.append(hit[OUT_COL_APPLICANT])
            if any(hit.values()):
                matched += 1

        df[OUT_COL_TITLE] = titles
        df[OUT_COL_BARCODE] = barcodes
        df[OUT_COL_APPLICANT] = applicants

        with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=EXCEL_SHEET, index=False)
            try:
                book = pd.ExcelFile(EXCEL_FILE)
                for name in book.sheet_names:
                    if name == EXCEL_SHEET:
                        continue
                    pd.read_excel(EXCEL_FILE, sheet_name=name, header=None).to_excel(
                        writer, sheet_name=name, index=False, header=False
                    )
            except Exception as exc:
                print(f"警告: 复制其他工作表失败: {exc}")

        print("\n========== 完成 ==========")
        print(f"总行数:   {len(df)}")
        print(f"匹配成功: {matched}")
        print(f"未匹配:   {len(df) - matched}")
        print(f"输出文件: {OUTPUT_FILE}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
