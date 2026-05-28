import requests
import json
import os
import re
import time
from urllib.parse import unquote
from datetime import datetime, timedelta

# ==================== 配置区 ====================
BASE_SAVE_PATH = "/home/tongtech/ODP/contract"  # 与合同、发票脚本保持一致

# 自动获取昨天的日期范围（00:00 - 23:59）
yesterday = datetime.now() - timedelta(days=1)
START_DATE = yesterday.strftime("%Y-%m-%d 00:00")
END_DATE = yesterday.strftime("%Y-%m-%d 23:59")
PAGE_SIZE = 20
RETRY_TIMES = 3
DOWNLOAD_DELAY = 0.5
# ===============================================
# 统一必须存在的8个子文件夹（顺序可随意）
REQUIRED_SUBDIRS = [
    "中标通知书",
    "合同电子版",
    "合同电子版客户水印版",
    "合同扫描件",
    "合同关键页扫描件",
    "发票扫描件",
    "里程碑验收",
    "回款凭证"
]

def sanitize_filename(filename):
    filename = str(filename)
    filename = re.sub(r'[\/:*?"<>|]', '_', filename)
    filename = filename.strip(" .")
    if len(filename) > 200:
        filename = filename[:200]
    return filename if filename else "未命名文件"

def download_file(url, save_path, authorization):
    for attempt in range(RETRY_TIMES):
        try:
            headers = {"Authorization": authorization}
            response = requests.get(url, headers=headers, timeout=60, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                status = "覆盖" if os.path.exists(save_path) else "新建"
                print(f" 下载成功（{status}）: {os.path.basename(save_path)}")
                return True
            else:
                print(f" 下载失败 [{attempt+1}/{RETRY_TIMES}]: HTTP {response.status_code}")
        except Exception as e:
            print(f" 下载异常 [{attempt+1}/{RETRY_TIMES}]: {e}")
        time.sleep(2)
    print(f" 下载最终失败: {url}")
    return False

# ==================== 主程序开始 ====================
os.makedirs(BASE_SAVE_PATH, exist_ok=True)
print(f"文件将保存至: {BASE_SAVE_PATH}\n")
print(f"查询回款日期范围: {START_DATE} ~ {END_DATE}\n")

# 获取 token（与之前脚本通用）
token_url = "https://user.zdsztech.com/employee-web-application/systemCert/getTokenInfo"
token_payload = {
    "accessId": "3eJB4n5Yc8",
    "accessSecretKey": "1b595cfea4c468b0e9eda16cf3563e17"
}
print("正在获取 token...")
resp_token = requests.post(token_url, json=token_payload, timeout=30)
if resp_token.status_code != 200:
    print(f"获取 token 失败，HTTP 状态码: {resp_token.status_code}")
    print(resp_token.text)
    exit()

token_json = resp_token.json()
if token_json.get("code") != "200" or not token_json.get("success"):
    print("获取 token 返回业务失败:", token_json.get("message"))
    exit()

authorization = token_json["data"]["accessToken"]
print("token 获取成功\n")

# 回款查询接口
query_url = "https://api.zdsztech.com/employee-web-application/external/queryData/xr9Whzk5tM"
headers = {
    "Authorization": authorization,
    "Content-Type": "application/json"
}

page_num = 1
total_downloaded = 0
processed_payments = 0  # 处理的回款单数量

while True:
    query_payload = {
        "type": "Payment",
        "startDate": START_DATE,
        "endDate": END_DATE,
        "pageNum": page_num,
        "pageSize": PAGE_SIZE
    }
    print(f"正在查询第 {page_num} 页回款数据...")
    resp_query = requests.post(query_url, json=query_payload, headers=headers, timeout=30)
    if resp_query.status_code != 200:
        print(f"查询回款失败，HTTP 状态码: {resp_query.status_code}")
        print(resp_query.text)
        break

    query_json = resp_query.json()
    if query_json.get("code") != "200" or not query_json.get("success"):
        print("查询回款返回业务失败:", query_json.get("message"))
        break

    data = query_json["data"]
    rows = data["rows"]
    total = int(data["total"])
    print(f"本页获取 {len(rows)} 条记录，总计 {total} 条\n")

    if not rows:
        print("已无更多数据")
        break

    for item in rows:
        payment_receipt_number = item.get("PaymentReceipt Number", "未知回款单号")
        payment_details = item.get("PaymentDetails", [])  # 可能多个合同
        payment_receipts = item.get("PaymentReceipt", [])  # 回款附件列表

        if not payment_details:
            print(f"回款单 {payment_receipt_number} 无关联合同，跳过")
            processed_payments += 1
            continue

        if not payment_receipts:
            print(f"回款单 {payment_receipt_number} 无附件")
            processed_payments += 1
            continue

        # 对同一个回款单的附件，需要复制到每个关联的合同文件夹下
        for detail in payment_details:
            contract_no = detail.get("contractNo", "未知合同号")
            contract_name = detail.get("contractName", "未知合同名称")

            main_folder_name = sanitize_filename(f"{contract_no}_{contract_name}")
            main_dir = os.path.join(BASE_SAVE_PATH, main_folder_name)
            os.makedirs(main_dir, exist_ok=True)

        # === 新增：统一创建8个必须的子文件夹 ===
        for sub_name in REQUIRED_SUBDIRS:
            sub_dir = os.path.join(main_dir, sub_name)
            if not os.path.exists(sub_dir):
                os.makedirs(sub_dir)

            sub_name = "回款凭证"
            sub_dir = os.path.join(main_dir, sub_name)
            

            print(f"处理回款单 {payment_receipt_number} → 合同文件夹: {main_folder_name}")

            for file_info in payment_receipts:
                name = file_info.get("name")
                url = file_info.get("url")
                if not name or not url:
                    continue

                name = unquote(name)
                filename = sanitize_filename(name)
                save_path = os.path.join(sub_dir, filename)

                print(f"下载 [{sub_name}] {filename}")
                if download_file(url, save_path, authorization):
                    total_downloaded += 1
                time.sleep(DOWNLOAD_DELAY)

            print(f"√ 回款凭证已放入: {main_folder_name}\n")

        processed_payments += 1

    if page_num * PAGE_SIZE >= total:
        break
    page_num += 1

print("=" * 60)
print(f"全部完成！")
print(f"处理回款单数量: {processed_payments}")
print(f"成功下载文件数量: {total_downloaded}")
print(f"文件保存路径: {BASE_SAVE_PATH}")
print("=" * 60)