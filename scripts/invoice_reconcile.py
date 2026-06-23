#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地发票核对脚本：Excel 明细/汇总 vs 数据库入库表。

数据不进入 Git：脚本在本机直连数据库，结果写到本地 output 目录（已 gitignore）。

用法:
  pip install pandas openpyxl pymysql pyyaml

  # 1. 复制配置并填写表名、字段映射
  cp scripts/invoice_reconcile.local.yaml.example scripts/invoice_reconcile.local.yaml

  # 2. 运行（默认明细核对：按发票唯一键）
  python scripts/invoice_reconcile.py

  # 仅核对透视表汇总
  python scripts/invoice_reconcile.py --mode summary

  # 指定 Excel 路径
  python scripts/invoice_reconcile.py --excel "src/main/java/com/example/demo/2023年取得发票.xlsx"
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
import pymysql
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "scripts" / "invoice_reconcile.local.yaml"
DEFAULT_EXCEL = ROOT / "src/main/java/com/example/demo/2023年取得发票.xlsx"
OUTPUT_DIR = ROOT / "scripts" / "output"


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        print(f"缺少配置文件: {path}")
        print("请先复制 invoice_reconcile.local.yaml.example 并填写数据库与字段映射。")
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_str(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if text in ("--", "nan", "None", "NaT"):
        return ""
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def invoice_key(
    digital_no: Any,
    invoice_code: Any,
    invoice_no: Any,
) -> Optional[str]:
    digital = normalize_str(digital_no)
    if digital:
        return f"D:{digital}"
    code = normalize_str(invoice_code)
    number = normalize_str(invoice_no)
    if code or number:
        return f"C:{code}_{number}"
    return None


def read_excel_detail(excel_path: Path, exclude_void: bool) -> pd.DataFrame:
    df = pd.read_excel(excel_path, sheet_name="Sheet1", header=0)
    if exclude_void and "发票状态" in df.columns:
        df = df[~df["发票状态"].astype(str).str.contains("作废", na=False)]
    df = df.copy()
    df["__inv_key"] = df.apply(
        lambda r: invoice_key(r.get("数电发票号码"), r.get("发票代码"), r.get("发票号码")),
        axis=1,
    )
    return df


def aggregate_invoice_amount(df: pd.DataFrame, amount_col: str) -> pd.DataFrame:
    grouped = (
        df.dropna(subset=["__inv_key"])
        .groupby("__inv_key", as_index=False)[amount_col]
        .sum()
        .rename(columns={amount_col: "excel_amount"})
    )
    return grouped


def read_excel_summary(excel_path: Path) -> pd.DataFrame:
    pivot = pd.read_excel(excel_path, sheet_name="透视表", header=None)
    header_row = pivot.iloc[3]
    data = pivot.iloc[4:].copy()
    data.columns = ["invoice_type", *header_row.iloc[1:].tolist()]
    data = data.rename(columns={data.columns[-1]: "total"})
    value_cols = [c for c in data.columns if c not in ("invoice_type", "total")]
    long_df = data.melt(
        id_vars=["invoice_type"],
        value_vars=value_cols,
        var_name="category",
        value_name="excel_amount",
    )
    long_df = long_df[long_df["invoice_type"].astype(str) != "总计"]
    long_df = long_df.dropna(subset=["excel_amount"])
    long_df["excel_amount"] = pd.to_numeric(long_df["excel_amount"], errors="coerce")
    long_df = long_df.dropna(subset=["excel_amount"])
    long_df["category"] = long_df["category"].astype(str).str.strip()
    long_df["invoice_type"] = long_df["invoice_type"].astype(str).str.strip()
    return long_df


def connect_mysql(db_cfg: Dict[str, Any]) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=db_cfg["host"],
        port=int(db_cfg.get("port", 3306)),
        user=db_cfg["user"],
        password=db_cfg["password"],
        database=db_cfg["database"],
        charset=db_cfg.get("charset", "utf8mb4"),
        cursorclass=pymysql.cursors.SSCursor,
    )


def build_select_sql(cfg: Dict[str, Any], mode: str) -> Tuple[str, List[Any]]:
    table = cfg["table"]
    fields = cfg["fields"]
    where = cfg.get("where", "1=1")
    params: List[Any] = []

    digital = fields["digital_invoice_no"]
    code = fields["invoice_code"]
    number = fields["invoice_no"]
    amount = fields["amount"]
    invoice_type = fields["invoice_type"]
    status = fields.get("invoice_status")
    category = fields.get("category")
    invoice_date = fields.get("invoice_date")

    if mode == "summary":
        if not category:
            raise ValueError("summary 模式需要在配置 fields 中填写 category（大类字段）")
        status_filter = ""
        if status and cfg.get("exclude_void_in_db", True):
            status_filter = f" AND ({status} NOT LIKE '%作废%' OR {status} IS NULL)"
        sql = f"""
            SELECT {invoice_type} AS invoice_type,
                   {category} AS category,
                   SUM({amount}) AS db_amount
            FROM {table}
            WHERE {where}{status_filter}
            GROUP BY {invoice_type}, {category}
        """
        return sql, params

    select_cols = [
        f"{digital} AS digital_invoice_no",
        f"{code} AS invoice_code",
        f"{number} AS invoice_no",
        f"{amount} AS amount",
    ]
    if invoice_type:
        select_cols.append(f"{invoice_type} AS invoice_type")
    if status:
        select_cols.append(f"{status} AS invoice_status")
    if category:
        select_cols.append(f"{category} AS category")
    if invoice_date:
        select_cols.append(f"{invoice_date} AS invoice_date")

    status_filter = ""
    if status and cfg.get("exclude_void_in_db", True):
        status_filter = f" AND ({status} NOT LIKE '%作废%' OR {status} IS NULL)"

    sql = f"""
        SELECT {", ".join(select_cols)}
        FROM {table}
        WHERE {where}{status_filter}
    """
    return sql, params


def fetch_db_detail(conn: pymysql.connections.Connection, sql: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    with conn.cursor() as cursor:
        cursor.execute(sql)
        columns = [d[0] for d in cursor.description]
        while True:
            batch = cursor.fetchmany(5000)
            if not batch:
                break
            for row in batch:
                rows.append(dict(zip(columns, row)))
    return pd.DataFrame(rows)


def fetch_db_summary(conn: pymysql.connections.Connection, sql: str) -> pd.DataFrame:
    with conn.cursor() as cursor:
        cursor.execute(sql)
        columns = [d[0] for d in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    df = pd.DataFrame(data)
    if not df.empty:
        df["db_amount"] = pd.to_numeric(df["db_amount"], errors="coerce")
    return df


def compare_detail(excel_df: pd.DataFrame, db_df: pd.DataFrame, amount_col: str) -> Dict[str, pd.DataFrame]:
    excel_amount = aggregate_invoice_amount(excel_df, amount_col)
    excel_keys: Set[str] = set(excel_amount["__inv_key"])

    db_df = db_df.copy()
    db_df["__inv_key"] = db_df.apply(
        lambda r: invoice_key(r.get("digital_invoice_no"), r.get("invoice_code"), r.get("invoice_no")),
        axis=1,
    )
    db_amount = (
        db_df.dropna(subset=["__inv_key"])
        .groupby("__inv_key", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "db_amount"})
    )
    db_keys: Set[str] = set(db_amount["__inv_key"])

    only_excel = excel_amount[~excel_amount["__inv_key"].isin(db_keys)].copy()
    only_db = db_amount[~db_amount["__inv_key"].isin(excel_keys)].copy()

    merged = excel_amount.merge(db_amount, on="__inv_key", how="inner")
    merged["diff"] = merged["excel_amount"] - merged["db_amount"]
    amount_mismatch = merged[merged["diff"].abs() > 0.01].copy()

    return {
        "only_in_excel": only_excel.sort_values("excel_amount", ascending=False),
        "only_in_db": only_db.sort_values("db_amount", ascending=False),
        "amount_mismatch": amount_mismatch.sort_values("diff", key=lambda s: s.abs(), ascending=False),
        "summary": pd.DataFrame(
            [
                {
                    "excel_invoice_count": len(excel_keys),
                    "db_invoice_count": len(db_keys),
                    "matched_count": len(excel_keys & db_keys),
                    "only_in_excel_count": len(excel_keys - db_keys),
                    "only_in_db_count": len(db_keys - excel_keys),
                    "amount_mismatch_count": len(amount_mismatch),
                }
            ]
        ),
    }


def compare_summary(excel_summary: pd.DataFrame, db_summary: pd.DataFrame) -> pd.DataFrame:
    merged = excel_summary.merge(
        db_summary,
        on=["invoice_type", "category"],
        how="outer",
        indicator=True,
    )
    merged["excel_amount"] = merged["excel_amount"].fillna(0)
    merged["db_amount"] = merged["db_amount"].fillna(0)
    merged["diff"] = merged["excel_amount"] - merged["db_amount"]
    return merged.sort_values(["invoice_type", "category"])


def write_reports(prefix: str, frames: Dict[str, pd.DataFrame]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUTPUT_DIR / f"{prefix}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False, encoding="utf-8-sig")
    return out_dir


def print_detail_summary(frames: Dict[str, pd.DataFrame]) -> None:
    s = frames["summary"].iloc[0]
    print("\n========== 明细核对结果 ==========")
    print(f"Excel 唯一发票数: {int(s['excel_invoice_count'])}")
    print(f"数据库唯一发票数: {int(s['db_invoice_count'])}")
    print(f"两边都有:         {int(s['matched_count'])}")
    print(f"仅在 Excel:       {int(s['only_in_excel_count'])}")
    print(f"仅在数据库:       {int(s['only_in_db_count'])}")
    print(f"金额不一致:       {int(s['amount_mismatch_count'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description="本地发票 Excel vs 数据库入库表核对")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    parser.add_argument("--mode", choices=["detail", "summary"], default="detail")
    args = parser.parse_args()

    cfg = load_config(args.config)
    excel_path = args.excel
    if not excel_path.exists():
        print(f"Excel 不存在: {excel_path}")
        sys.exit(1)

    print(f"连接数据库 {cfg['database']['host']} / {cfg['database']['database']} ...")
    conn = connect_mysql(cfg["database"])
    try:
        sql, _ = build_select_sql(cfg, args.mode)
        print("执行 SQL 查询（流式读取，无需导出全表）...")

        if args.mode == "detail":
            excel_df = read_excel_detail(excel_path, cfg.get("exclude_void_in_excel", True))
            db_df = fetch_db_detail(conn, sql)
            frames = compare_detail(excel_df, db_df, amount_col="价税合计")
            print_detail_summary(frames)
            out = write_reports("detail", frames)
        else:
            excel_summary = read_excel_summary(excel_path)
            db_summary = fetch_db_summary(conn, sql)
            merged = compare_summary(excel_summary, db_summary)
            mismatch = merged[merged["diff"].abs() > 0.01]
            frames = {
                "summary_compare": merged,
                "summary_mismatch": mismatch,
            }
            print("\n========== 汇总核对结果 ==========")
            print(f"透视表组合数: {len(excel_summary)}")
            print(f"数据库组合数: {len(db_summary)}")
            print(f"金额不一致项: {len(mismatch)}")
            out = write_reports("summary", frames)

        print(f"\n结果已写入: {out}")
        print("（该目录已在 .gitignore 中，不会提交到 Git）")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
