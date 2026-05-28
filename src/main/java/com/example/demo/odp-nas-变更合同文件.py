import requests
import json
import os
import re
import time
from urllib.parse import unquote
from datetime import datetime, timedelta

# ==================== 配置区 ====================
# 保存路径（保持与原合同脚本一致）
BASE_SAVE_PATH = "/home/tongtech/ODP/contract"

# 自动获取昨天的日期范围（可手动覆盖）
yesterday = datetime.now() - timedelta(days=1)
START_DATE = yesterday.strftime("%Y-%m-%d")     # 如 2026-01-22
END_DATE   = yesterday.strftime("%Y-%m-%d")

# START_DATE = "2026-01-23"   # 如需全量/指定范围，取消注释手动设置
# END_DATE   = "2026-01-23"

PAGE_SIZE = 20              # 建议 20~50
RETRY_TIMES = 3
DOWNLOAD_DELAY = 0.5        # 防限流

# 统一必须存在的 8 个子文件夹
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

# ===============================================

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
                existed = os.path.exists(save_path)  # 下载前已存在→覆盖
                print(f" 下载成功（{'覆盖' if existed else '新建'}）: {os.path.basename(save_path)}")
                return True
            else:
                print(f" 下载失败 [{attempt+1}/{RETRY_TIMES}]: HTTP {response.status_code}")
        except Exception as e:
            print(f" 下载异常 [{attempt+1}/{RETRY_TIMES}]: {e}")
        time.sleep(2)
    print(f" 下载最终失败: {url}")
    return False


# ==================== 主程序 ====================
os.makedirs(BASE_SAVE_PATH, exist_ok=True)
print(f"变更附件将保存至: {BASE_SAVE_PATH}\n")

# 获取 token（与原脚本相同）
token_url = "https://user.zdsztech.com/employee-web-application/systemCert/getTokenInfo"
token_payload = {
    "accessId": "3eJB4n5Yc8",
    "accessSecretKey": "1b595cfea4c468b0e9eda16cf3563e17"
}
print("正在获取 token...")
resp_token = requests.post(token_url, json=token_payload, timeout=30)
if resp_token.status_code != 200 or not resp_token.json().get("success"):
    print("获取 token 失败")
    print(resp_token.text)
    exit()

authorization = resp_token.json()["data"]["accessToken"]
print("token 获取成功\n")

# 新接口：合同变更附件
query_url = "https://api.zdsztech.com/employee-web-application/external/queryData/3mX5W27ow6"
headers = {
    "Authorization": authorization,
    "Content-Type": "application/json"
}

page_num = 1
total_downloaded = 0
processed_contracts = 0

while True:
    query_payload = {
        "type": "Attachment",           # ← 改这里
        "startDate": START_DATE + " 00:00",
        "endDate": END_DATE + " 23:59",
        "pageNum": page_num,
        "pageSize": PAGE_SIZE
    }

    print(f"正在查询变更附件 第 {page_num} 页...")
    resp_query = requests.post(query_url, json=query_payload, headers=headers, timeout=30)

    if resp_query.status_code != 200:
        print(f"查询失败 HTTP {resp_query.status_code}")
        print(resp_query.text)
        break

    query_json = resp_query.json()
    if query_json.get("code") != "200" or not query_json.get("success"):
        print("查询返回业务失败:", query_json.get("message"))
        break

    data = query_json["data"]
    rows = data.get("rows", [])
    total = int(data.get("total", 0))

    print(f"本页 {len(rows)} 条，总计 {total} 条\n")

    if not rows:
        break

    for item in rows:
        contract_no = item.get("contractNo", "未知编号")
        contract_name = item.get("contractName", "未知名称")

        main_folder_name = sanitize_filename(f"{contract_no}_{contract_name}")
        main_dir = os.path.join(BASE_SAVE_PATH, main_folder_name)
        os.makedirs(main_dir, exist_ok=True)

        # 统一创建 8 个子文件夹
        for sub_name in REQUIRED_SUBDIRS:
            sub_dir = os.path.join(main_dir, sub_name)
            os.makedirs(sub_dir, exist_ok=True)

        # 变更附件也使用相同的四个字段（结构一致）
        sub_dirs = {
            "合同电子版": item.get("electronicContractUrl", []),
            "合同电子版客户水印版": item.get("watermarkedContractUrl", []),
            "中标通知书": item.get("bidNoticeUrl", []),
            "合同扫描件": item.get("contractScanUrl", [])
        }

        for sub_name, file_list in sub_dirs.items():
            if not file_list:
                continue
            sub_dir = os.path.join(main_dir, sub_name)
            for file_info in file_list:
                name = file_info.get("name")
                url = file_info.get("url")
                if not name or not url:
                    continue

                name = unquote(name)
                filename = sanitize_filename(name)
                save_path = os.path.join(sub_dir, filename)

                print(f"下载 [变更-{sub_name}] {filename}")
                if download_file(url, save_path, authorization):
                    total_downloaded += 1
                time.sleep(DOWNLOAD_DELAY)

        processed_contracts += 1
        print(f"√ 变更附件处理完成: {main_folder_name}\n")

    if page_num * PAGE_SIZE >= total:
        break
    page_num += 1

print("=" * 60)
print("变更附件同步全部完成！")
print(f"处理合同数量: {processed_contracts}")
print(f"成功下载文件数量: {total_downloaded}")
print(f"保存路径: {BASE_SAVE_PATH}")
print("=" * 60)