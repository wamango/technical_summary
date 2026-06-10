import requests
import os
import re
import time
from urllib.parse import unquote
from datetime import datetime, timedelta

# ==================== 配置区 ====================
# 请修改为你的实际保存路径（NAS挂载点或本地目录）
BASE_SAVE_PATH = "/home/tongtech/ODP/contract"  # Linux 示例路径
# 自动获取昨天的日期范围（00:00 - 23:59）
yesterday = datetime.now() - timedelta(days=1)
START_DATE = yesterday.strftime("%Y-%m-%d")   # 例如: 2025-12-23
END_DATE = yesterday.strftime("%Y-%m-%d")     # 例如: 2025-12-23
# START_DATE = "2026-01-01"
# END_DATE = "2026-01-14"
# 每页查询条数（建议 20~50）
PAGE_SIZE = 20
# 下载失败重试次数
RETRY_TIMES = 3
# 下载间隔（秒），防止被接口限流
DOWNLOAD_DELAY = 0.5
# 扣款依据子文件夹名称
SUB_DIR_NAME = "扣款依据"
# 接口返回的扣款依据附件字段名（如与实际不符请修改）
DEDUCTION_BASIS_FIELD = "deductionBasisUrl"
# ===============================================


def sanitize_filename(filename):
    filename = str(filename)
    filename = re.sub(r'[\/:*?"<>|]', '_', filename)
    filename = filename.strip(" .")
    if len(filename) > 200:
        filename = filename[:200]
    return filename if filename else "未命名文件"


def get_unique_save_path(directory, filename):
    """同名文件不覆盖，自动追加 -1、-2 后缀。"""
    save_path = os.path.join(directory, filename)
    if not os.path.exists(save_path):
        return save_path

    name, ext = os.path.splitext(filename)
    counter = 1
    while True:
        candidate = f"{name}-{counter}{ext}"
        save_path = os.path.join(directory, candidate)
        if not os.path.exists(save_path):
            return save_path
        counter += 1


def ensure_deduction_dir(main_dir):
    """仅在当前合同下不存在「扣款依据」文件夹时创建。"""
    sub_dir = os.path.join(main_dir, SUB_DIR_NAME)
    if not os.path.exists(sub_dir):
        os.makedirs(sub_dir)
    return sub_dir


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
                print(f" 下载成功: {os.path.basename(save_path)}")
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

query_url = "https://api.zdsztech.com/employee-web-application/external/queryData/FXmiJ65u06"
headers = {
    "Authorization": authorization,
    "Content-Type": "application/json"
}

page_num = 1
total_downloaded = 0
processed_contracts = 0

while True:
    query_payload = {
        "type": "date",
        "startDate": START_DATE,
        "endDate": END_DATE,
        "pageNum": page_num,
        "pageSize": PAGE_SIZE
    }
    print(f"正在查询第 {page_num} 页合同数据...")
    resp_query = requests.post(query_url, json=query_payload, headers=headers, timeout=30)
    if resp_query.status_code != 200:
        print(f"查询合同失败，HTTP 状态码: {resp_query.status_code}")
        print(resp_query.text)
        break

    query_json = resp_query.json()
    if query_json.get("code") != "200" or not query_json.get("success"):
        print("查询合同返回业务失败:", query_json.get("message"))
        break

    data = query_json["data"]
    rows = data["rows"]
    total = int(data["total"])
    print(f"本页获取 {len(rows)} 条记录，总计 {total} 条\n")

    if not rows:
        print("已无更多数据")
        break

    for item in rows:
        file_list = item.get(DEDUCTION_BASIS_FIELD, [])
        if not file_list:
            continue

        contract_no = item.get("contractNo", "未知合同号")
        contract_name = item.get("contractName", "未知合同名称")
        main_folder_name = sanitize_filename(f"{contract_no}_{contract_name}")
        main_dir = os.path.join(BASE_SAVE_PATH, main_folder_name)
        os.makedirs(main_dir, exist_ok=True)
        sub_dir = ensure_deduction_dir(main_dir)

        for file_info in file_list:
            name = file_info.get("name")
            url = file_info.get("url")
            if not name or not url:
                continue

            name = unquote(name)
            filename = sanitize_filename(name)
            save_path = get_unique_save_path(sub_dir, filename)

            print(f"下载 [{SUB_DIR_NAME}] {os.path.basename(save_path)}")
            if download_file(url, save_path, authorization):
                total_downloaded += 1
            time.sleep(DOWNLOAD_DELAY)

        processed_contracts += 1
        print(f"√ 合同处理完成: {main_folder_name}\n")

    if page_num * PAGE_SIZE >= total:
        break
    page_num += 1

print("=" * 60)
print("全部完成！")
print(f"处理合同数量: {processed_contracts}")
print(f"成功下载文件数量: {total_downloaded}")
print(f"文件保存路径: {BASE_SAVE_PATH}")
print("=" * 60)
