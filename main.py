import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Drive API 認証
def authenticate_drive():
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

# Google Calendar API 認証
def authenticate_calendar():
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    return build("calendar", "v3", credentials=creds)

# 日本の祝日を取得
def get_japanese_holidays(year, month, creds):
    calendar = authenticate_calendar()
    time_min = datetime.datetime(year, month, 1).isoformat() + "Z"
    if month == 12:
        time_max = datetime.datetime(year + 1, 1, 1).isoformat() + "Z"
    else:
        time_max = datetime.datetime(year, month + 1, 1).isoformat() + "Z"

    events_result = calendar.events().list(
        calendarId="ja.japanese#holiday@group.v.calendar.google.com",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    holidays = [
        event["start"]["date"]
        for event in events_result.get("items", [])
        if "start" in event and "date" in event["start"]
    ]
    return holidays

# フォルダの存在確認または作成
def get_folder_id(service, name, parent_id):
    query = f"'{parent_id}' in parents and name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])
    if folders:
        return folders[0]["id"]
    else:
        return create_folder(service, name, parent_id)

def create_folder(service, name, parent_id):
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = service.files().create(body=file_metadata).execute()
    return folder["id"]

# 平日のフォルダ作成
def create_weekday_folders(service, parent_folder_id, year, month, holidays):
    month_str = f"{year}{month:02d}"
    month_folder_id = get_folder_id(service, month_str, parent_folder_id)

    date = datetime.date(year, month, 1)
    while date.month == month:
        if date.weekday() < 5:  # 平日
            date_str = date.isoformat()
            if date_str not in holidays:
                folder_name = f"{date.strftime('%Y%m%d')}_"
                get_folder_id(service, folder_name, month_folder_id)
        date += datetime.timedelta(days=1)

# メイン関数
def main():
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/calendar.readonly"]
    )

    drive_service = build("drive", "v3", credentials=creds)
    year = datetime.date.today().year
    month = datetime.date.today().month + 1
    if month == 13:
        year += 1
        month = 1

    PARENT_FOLDER_ID = os.environ["PARENT_FOLDER_ID"]
    holidays = get_japanese_holidays(year, month, creds)
    create_weekday_folders(drive_service, PARENT_FOLDER_ID, year, month, holidays)

if __name__ == "__main__":
    main()
