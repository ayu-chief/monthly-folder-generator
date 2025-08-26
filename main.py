import os
import json
import calendar
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Driveの親フォルダID（変更不要）
PARENT_FOLDER_ID = "1DCrKM6IUe7B_1M_3lf84iJ8MEd7d3rfU"

def get_service_account_credentials():
    # GitHub Secrets の GCP_SERVICE_ACCOUNT を使うよう統一
    service_account_info = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])
    return service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )

def create_folder(service, name, parent_id):
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    print(f"✅ フォルダ作成: {name}（ID: {folder.get('id')}）")
    return folder.get("id")

def folder_exists(service, name, parent_id):
    query = (
        f"mimeType='application/vnd.google-apps.folder' and "
        f"name='{name}' and "
        f"'{parent_id}' in parents and trashed = false"
    )
    results = service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    return len(results.get("files", [])) > 0

def generate_monthly_folders():
    credentials = get_service_account_credentials()
    service = build("drive", "v3", credentials=credentials)

    now = datetime.now()
    year = now.year
    month = now.month + 1  # 翌月

    if month > 12:
        year += 1
        month = 1

    # 月フォルダ名（例: 2025_09）
    month_folder_name = f"{year}_{str(month).zfill(2)}"

    if folder_exists(service, month_folder_name, PARENT_FOLDER_ID):
        print(f"⚠️ フォルダ「{month_folder_name}」はすでに存在します。スキップします。")
        return

    # 月フォルダ作成
    month_folder_id = create_folder(service, month_folder_name, PARENT_FOLDER_ID)

    # 平日のみ日別フォルダを作成
    num_days = calendar.monthrange(year, month)[1]
    for day in range(1, num_days + 1):
        date_obj = datetime(year, month, day)
        weekday = date_obj.weekday()  # 月曜:0, 日曜:6

        if weekday < 5:  # 平日のみ（0〜4）
            day_folder_name = f"{str(day).zfill(2)}_{calendar.day_name[weekday]}"
            create_folder(service, day_folder_name, month_folder_id)

def main():
    generate_monthly_folders()

if __name__ == "__main__":
    main()
