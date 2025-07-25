
import os
import calendar
import datetime
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# === 設定 ===
YEAR = 2025
MONTH = 8
PARENT_FOLDER_ID = "1DCrKM6IUe7B_1M_3lf84iJ8MEd7d3rfU"

# 日本の祝日API（Google Calendar APIの祝日カレンダー）
def get_japanese_holidays(year, month):
    calendar_id = "ja.japanese#holiday@group.v.calendar.google.com"
    time_min = f"{year}-{str(month).zfill(2)}-01T00:00:00Z"
    time_max = f"{year}-{str(month).zfill(2)}-31T23:59:59Z"

    creds = Credentials.from_service_account_file(
        "service_account.json",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    service = build("calendar", "v3", credentials=creds)

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    holidays = set()
    for event in events_result.get("items", []):
        date = event["start"]["date"]
        holidays.add(datetime.datetime.strptime(date, "%Y-%m-%d").date())
    return holidays

def get_weekday_dates(year, month, holidays):
    weekdays = []
    _, num_days = calendar.monthrange(year, month)
    for day in range(1, num_days + 1):
        date = datetime.date(year, month, day)
        if date.weekday() < 5 and date not in holidays:
            weekdays.append(date.strftime("%Y%m%d_"))
    return weekdays

def create_service():
    creds = Credentials.from_service_account_file(
        "service_account.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def create_folder(service, name, parent_id):
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")

def get_folder_id(service, name, parent_id):
    query = f"'{parent_id}' in parents and name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])
    return folders[0]["id"] if folders else None

def main():
    service = create_service()

    # 月フォルダ作成
    month_folder_name = f"{YEAR}{str(MONTH).zfill(2)}"
    month_folder_id = get_folder_id(service, month_folder_name, PARENT_FOLDER_ID)
    if not month_folder_id:
        month_folder_id = create_folder(service, month_folder_name, PARENT_FOLDER_ID)

    # 祝日取得
    holidays = get_japanese_holidays(YEAR, MONTH)

    # 平日フォルダ作成
    for folder_name in get_weekday_dates(YEAR, MONTH, holidays):
        if not get_folder_id(service, folder_name, month_folder_id):
            create_folder(service, folder_name, month_folder_id)
            print(f"作成: {folder_name}")

if __name__ == "__main__":
    main()
