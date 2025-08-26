import os
import json
import calendar
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Drive API 認証情報を GitHub Secrets から取得
def get_service_account_credentials():
    service_account_info = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])
    return service_account.Credentials.from_service_account_info(service_account_info)

# フォルダを作成する関数
def create_folder(drive_service, folder_name, parent_id):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    file = drive_service.files().create(body=file_metadata, fields='id').execute()
    return file.get('id')

# 指定フォルダ配下にフォルダが存在するかチェック
def get_folder_id(drive_service, folder_name, parent_id):
    query = f"'{parent_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    return items[0]['id'] if items else None

# 日本の祝日を取得
def get_japanese_holidays(year, month, creds):
    service = build("calendar", "v3", credentials=creds)
    time_min = f"{year}-{month:02d}-01T00:00:00Z"
    last_day = calendar.monthrange(year, month)[1]
    time_max = f"{year}-{month:02d}-{last_day}T23:59:59Z"
    events_result = service.events().list(
        calendarId="ja.japanese#holiday@group.v.calendar.google.com",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    holidays = [event["start"]["date"] for event in events_result.get("items", [])]
    return holidays

# メイン処理
def main():
    creds = get_service_account_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    PARENT_FOLDER_ID = os.environ["PARENT_FOLDER_ID"]

    # 次の月を計算
    today = datetime.today()
    year = today.year + (1 if today.month == 12 else 0)
    month = 1 if today.month == 12 else today.month + 1

    month_folder_name = f"{year}年{month}月"
    month_folder_id = get_folder_id(drive_service, month_folder_name, PARENT_FOLDER_ID)
    if not month_folder_id:
        month_folder_id = create_folder(drive_service, month_folder_name, PARENT_FOLDER_ID)

    holidays = get_japanese_holidays(year, month, creds)

    # 平日のみ（祝日を除く）
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    delta = timedelta(days=1)

    current_day = first_day
    while current_day <= last_day:
        if current_day.weekday() < 5 and current_day.strftime("%Y-%m-%d") not in holidays:
            folder_name = f"{current_day.month:02d}.{current_day.day:02d}（{['月','火','水','木','金'][current_day.weekday()]}）"
            get_or_create = get_folder_id(drive_service, folder_name, month_folder_id)
            if not get_or_create:
                create_folder(drive_service, folder_name, month_folder_id)
        current_day += delta

if __name__ == "__main__":
    main()
