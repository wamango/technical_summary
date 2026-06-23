#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票 Excel 回填脚本：按发票代码+号码（或数电发票号码）查询 t_biz_invoice，
将流程标题、流程条形码、流程申请人名称写回 Excel 对应行。

在服务器上运行（需能访问 10.10.80.52）:

  pip install -r scripts/requirements-invoice-reconcile.txt

  # 首次运行：查看表字段（确认映射是否正确）
  python scripts/invoice_enrich.py --show-columns

  # 执行回填（Excel 放服务器任意路径）
  python scripts/invoice_enrich.py --excel /data/2023年取得发票.xlsx

  # 指定输出文件
  python scripts/invoice_enrich.py --excel /data/2023年取得发票.xlsx --output /data/2023年取得发票_已匹配.xlsx

配置文件（含密码，不提交 Git）:
  scripts/invoice_enrich.local.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import pymysql
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "scripts" / "invoice_enrich.local.yaml"
DEFAULT_EXCEL = ROOT / "src/main/java/com/example/demo/2023年取得发票.xlsx"

OUT_COL_TITLE = "流程标题"
OUT_COL_BARCODE = "流程条形码"
OUT_COL_APPLICANT = "流程申请人名称"

# 字段自动探测候选（按优先级）
FIELD_CANDIDATES = {
    "invoice_code": [
        "invoice_code",
        "fpdm",
        "fapiao_code",
        "invoice_type_code",
        "type_code",
    ],
    "invoice_no": [
        "invoice_no",
        "invoice_number",
        "invoice_num",
        "fphm",
        "fapiao_no",
        "digital_invoice_no",
        "digital_invoice_number",
    ],
    "flow_title": [
        "flow_title",
        "process_title",
        "workflow_title",
        "bpm_title",
        "title",
        "process_name",
        "flow_name",
    ],
    "flow_barcode": [
        "flow_barcode",
        "process_barcode",
        "workflow_barcode",
        "bar_code",
        "barcode",
        "process_bar_code",
        "flow_bar_code",
    ],
    "apply_user_name": [
        "apply_user_name",
        "applicant_name",
        "process_apply_user_name",
        "flow_apply_user_name",
        "apply_name",
        "create_by_name",
        "applicant",
    ],
}


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        print(f"缺少配置文件: {path}")
        print("请复制 invoice_enrich.local.yaml.example 为 invoice_enrich.local.yaml 并填写密码。")
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_str(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if text in ("--", "nan", "None", "NaT"):
        return ""
    if re.fullmatch(r"\d+\.0", text):
        return text[:-2]
    return text


def connect_mysql(db_cfg: Dict[str, Any]) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=db_cfg["host"],
        port=int(db_cfg.get("port", 3306)),
        user=db_cfg["user"],
        password=db_cfg["password"],
        database=db_cfg["database"],
        charset=db_cfg.get("charset", "utf8mb4"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def list_table_columns(conn: pymysql.connections.Connection, table: str) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(f"SHOW COLUMNS FROM `{table}`")
        return [row["Field"] for row in cur.fetchall()]


def discover_field(columns: Sequence[str], logical_name: str, override: Optional[str]) -> Optional[str]:
    if override:
        if override not in columns:
            raise ValueError(f"配置的字段 {override} 不在表列中，可用列: {columns}")
        return override
    lower_map = {c.lower(): c for c in columns}
    for candidate in FIELD_CANDIDATES[logical_name]:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def resolve_fields(cfg: Dict[str, Any], conn: pymysql.connections.Connection) -> Dict[str, str]:
    table = cfg["table"]
    columns = list_table_columns(conn, table)
    overrides = cfg.get("fields") or {}
    resolved: Dict[str, str] = {}
    missing: List[str] = []
    for logical in FIELD_CANDIDATES:
        col = discover_field(columns, logical, overrides.get(logical))
        if col:
            resolved[logical] = col
        else:
            missing.append(logical)
    if missing:
        print("未能自动识别以下字段，请在 invoice_enrich.local.yaml 的 fields 中手动指定:")
        for name in missing:
            print(f"  - {name}")
        print("\n当前表全部列名:")
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
    table: str,
    fields: Dict[str, str],
    pairs: Sequence[Tuple[str, str]],
    numbers_only: Sequence[str],
    batch_size: int = 400,
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
        f"`{applicant_col}` AS apply_user_name FROM `{table}`"
    )

    with conn.cursor() as cur:
        for batch in chunked(list(pairs), batch_size):
            placeholders = ",".join(["(%s,%s)"] * len(batch))
            flat: List[str] = []
            for code, no in batch:
                flat.extend([code, no])
            sql = f"{select_sql} WHERE (`{code_col}`, `{no_col}`) IN ({placeholders})"
            cur.execute(sql, flat)
            for row in cur.fetchall():
                absorb(row)

        unique_numbers = sorted(set(numbers_only))
        for batch in chunked(unique_numbers, batch_size):
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
    return {OUT_COL_TITLE: "", OUT_COL_BARCODE: "", OUT_COL_APPLICANT: ""}


def enrich_excel(
    excel_path: Path,
    output_path: Path,
    conn: pymysql.connections.Connection,
    cfg: Dict[str, Any],
) -> None:
    sheet = cfg.get("excel_sheet", "Sheet1")
    print(f"读取 Excel: {excel_path} [{sheet}]")
    df = pd.read_excel(excel_path, sheet_name=sheet, header=0, dtype=object)

    required_cols = ["发票代码", "发票号码", "数电发票号码"]
    for col in required_cols:
        if col not in df.columns:
            print(f"Excel 缺少列: {col}，当前列: {list(df.columns)}")
            sys.exit(1)

    fields = resolve_fields(cfg, conn)

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

    pair_map, no_map = fetch_db_records(
        conn,
        cfg["table"],
        fields,
        pairs,
        numbers_only,
        batch_size=int(cfg.get("batch_size", 400)),
    )
    print(f"数据库命中: 代码+号码 {len(pair_map)} 组, 仅号码 {len(no_map)} 个")

    titles: List[str] = []
    barcodes: List[str] = []
    applicants: List[str] = []
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

    # 若列已存在则覆盖
    df[OUT_COL_TITLE] = titles
    df[OUT_COL_BARCODE] = barcodes
    df[OUT_COL_APPLICANT] = applicants

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet, index=False)
        # 保留原文件其他 sheet
        try:
            original = pd.ExcelFile(excel_path)
            for other in original.sheet_names:
                if other == sheet:
                    continue
                pd.read_excel(excel_path, sheet_name=other, header=None).to_excel(
                    writer, sheet_name=other, index=False, header=False
                )
        except Exception as exc:
            print(f"警告: 未能复制其他工作表: {exc}")

    print("\n========== 回填完成 ==========")
    print(f"总行数:   {len(df)}")
    print(f"匹配成功: {matched}")
    print(f"未匹配:   {len(df) - matched}")
    print(f"输出文件: {output_path}")


def show_columns(conn: pymysql.connections.Connection, table: str) -> None:
    columns = list_table_columns(conn, table)
    print(f"表 `{table}` 共 {len(columns)} 列:\n")
    for col in columns:
        print(col)
    print("\n建议 fields 配置示例（按实际列名修改）:")
    resolved = {}
    for logical in FIELD_CANDIDATES:
        resolved[logical] = discover_field(columns, logical, None) or "请手动填写"
    print(yaml.dump({"fields": resolved}, allow_unicode=True, sort_keys=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="发票 Excel 回填流程信息")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--show-columns", action="store_true", help="仅查看表字段并退出")
    args = parser.parse_args()

    cfg = load_config(args.config)
    db_cfg = cfg["database"]

    print(f"连接数据库 {db_cfg['host']}:{db_cfg.get('port', 3306)} / {db_cfg['database']} ...")
    conn = connect_mysql(db_cfg)
    try:
        if args.show_columns:
            show_columns(conn, cfg["table"])
            return

        excel_path = args.excel
        if not excel_path.exists():
            print(f"Excel 不存在: {excel_path}")
            sys.exit(1)

        if args.output:
            output_path = args.output
        else:
            output_path = excel_path.with_name(f"{excel_path.stem}_已匹配{excel_path.suffix}")

        enrich_excel(excel_path, output_path, conn, cfg)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
