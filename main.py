import os
import calendar
import datetime
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# === 設定 ===
PARENT_FOLDER_ID = "1DCrKM6IUe7B_1M_3lf84iJ8MEd7d3rfU"

# 今月の翌月を自動計算
today = datetime.date.today()
year = today.year + (today.month // 12)
month = (today.month % 12) + 1

# 日本の祝日取得
def get_japanese_holidays(year, month, creds):
    calendar_id = "ja.japanese#holiday@group.v.calendar.google.com"
    time_min = f"{year}-{str(month).zfill(2)}-01T00:00:00Z"
    time_max = f"{year}-{str(month).zfill(2)}-31T23:59:59Z"

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

def create_service_account_from_env():
    service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/calendar.readonly"]
    )
    return creds

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
    creds = create_service_account_from_env()
    drive_service = build("drive", "v3", credentials=creds)
    holidays = get_japanese_holidays(year, month, creds)

    month_folder_name = f"{year}{str(month).zfill(2)}"
    month_folder_id = get_folder_id(drive_service, month_folder_name, PARENT_FOLDER_ID)
    if not month_folder_id:
        month_folder_id = create_folder(drive_service, month_folder_name, PARENT_FOLDER_ID)

    for folder_name in get_weekday_dates(year, month, holidays):
        if not get_folder_id(drive_service, folder_name, month_folder_id):
            create_folder(drive_service, folder_name, month_folder_id)
            print(f"作成: {folder_name}")

if __name__ == "__main__":
    main()
