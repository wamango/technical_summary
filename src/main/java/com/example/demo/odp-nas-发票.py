import requests
import json
import os
import re
import time
from urllib.parse import unquote
from datetime import datetime, timedelta  # 用于自动计算昨天日期

# ==================== 配置区 ====================
# 保存路径（保持和合同脚本一致）
BASE_SAVE_PATH = "/home/tongtech/ODP/contract"  # 不要改这里
# 自动获取昨天的日期范围（00:00 - 23:59）
yesterday = datetime.now() - timedelta(days=1)
START_DATE = yesterday.strftime("%Y-%m-%d 00:00")   # 如: 2025-12-30 00:00
END_DATE = yesterday.strftime("%Y-%m-%d 23:59")     # 如: 2025-12-30 23:59

# 每页查询条数
PAGE_SIZE = 20
# 下载失败重试次数
RETRY_TIMES = 3
# 下载间隔（秒）
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

# 清理非法文件名字符
def sanitize_filename(filename):
    filename = str(filename)
    filename = re.sub(r'[\/:*?"<>|]', '_', filename)
    filename = filename.strip(" .")
    if len(filename) > 200:
        filename = filename[:200]
    return filename if filename else "未命名文件"

# 下载单个文件（直接覆盖同名文件）
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
                print(f" 下载成功（{'覆盖' if os.path.exists(save_path) else '新建'}）: {os.path.basename(save_path)}")
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
print(f"查询发票日期范围: {START_DATE} ~ {END_DATE}\n")

# 第一步：获取 token
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

# 第二步：发票查询接口
query_url = "https://api.zdsztech.com/employee-web-application/external/queryData/589rFofrI3"
headers = {
    "Authorization": authorization,
    "Content-Type": "application/json"
}

# 第三步：分页拉取所有发票并下载附件
page_num = 1
total_downloaded = 0
processed_invoices = 0

while True:
    query_payload = {
        "type": "Invoice",
        "startDate": START_DATE,
        "endDate": END_DATE,
        "pageNum": page_num,
        "pageSize": PAGE_SIZE
    }
    print(f"正在查询第 {page_num} 页发票数据...")
    resp_query = requests.post(query_url, json=query_payload, headers=headers, timeout=30)
    if resp_query.status_code != 200:
        print(f"查询发票失败，HTTP 状态码: {resp_query.status_code}")
        print(resp_query.text)
        break

    query_json = resp_query.json()
    if query_json.get("code") != "200" or not query_json.get("success"):
        print("查询发票返回业务失败:", query_json.get("message"))
        break

    data = query_json["data"]
    rows = data["rows"]
    total = int(data["total"])
    print(f"本页获取 {len(rows)} 条记录，总计 {total} 条\n")

    if not rows:
        print("已无更多数据")
        break

    for item in rows:
        # 使用合同号和合同名称作为主文件夹名（和原合同脚本一致）
        contract_no = item.get("contractNo", "未知合同号")
        contract_name = item.get("contractName", "未知合同名称")

        # 主文件夹：合同号_合同名称（保持原逻辑）
        main_folder_name = sanitize_filename(f"{contract_no}_{contract_name}")
        main_dir = os.path.join(BASE_SAVE_PATH, main_folder_name)
        os.makedirs(main_dir, exist_ok=True)  # 不存在则创建

        # === 新增：统一创建8个必须的子文件夹 ===
        for sub_name in REQUIRED_SUBDIRS:
            sub_dir = os.path.join(main_dir, sub_name)
            if not os.path.exists(sub_dir):
                os.makedirs(sub_dir)
            
        # 只创建一个子文件夹：发票扫描件
        sub_name = "发票扫描件"
        sub_dir = os.path.join(main_dir, sub_name)
       

        file_list = item.get("InvoiceAttachment", [])
        if not file_list:
            print(f"无附件: {main_folder_name}")
            processed_invoices += 1
            print(f"√ 发票处理完成（无附件）: {main_folder_name}\n")
            continue

        for file_info in file_list:
            name = file_info.get("name")
            url = file_info.get("url")
            if not name or not url:
                continue

            name = unquote(name)
            filename = sanitize_filename(name)
            save_path = os.path.join(sub_dir, filename)  # 直接覆盖同名文件

            print(f"下载 [{sub_name}] {filename}")
            if download_file(url, save_path, authorization):
                total_downloaded += 1
            time.sleep(DOWNLOAD_DELAY)

        processed_invoices += 1
        print(f"√ 发票处理完成: {main_folder_name}\n")

    # 是否还有下一页
    if page_num * PAGE_SIZE >= total:
        break
    page_num += 1

print("=" * 60)
print(f"全部完成！")
print(f"处理发票数量: {processed_invoices}")
print(f"成功下载文件数量: {total_downloaded}")
print(f"文件保存路径: {BASE_SAVE_PATH}")
print("=" * 60)