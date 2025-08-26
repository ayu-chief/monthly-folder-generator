import os
import json
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dateutil.relativedelta import relativedelta
import jpholiday

PARENT_FOLDER_ID = "1DCrKM6IUe7B_1M_3lf84iJ8MEd7d3rfU"

def get_service_account_credentials():
    service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])  # ← ここを修正！
    return service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )

def get_drive_service(creds):
    return build("drive", "v3", credentials=creds)

def get_weekdays(year, month):
    date = datetime.date(year, month, 1)
    weekdays = []
    while date.month == month:
        if date.weekday() < 5 and not jpholiday.is_holiday(date):
            weekdays.append(date.strftime("%Y-%m-%d"))
        date += datetime.timedelta(days=1)
    return weekdays

def find_folder(service, name, parent_id):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get("files", [])
    return items[0] if items else None

def create_folder(service, name, parent_id):
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    print(f"✅ フォルダ作成: {name}")
    return folder.get("id")

def main():
    creds = get_service_account_credentials()
    service = get_drive_service(creds)

    today = datetime.date.today()
    next_month = today + relativedelta(months=1)
    year = next_month.year
    month = next_month.month

    month_folder_name = f"{year}年{month:02d}月"
    month_folder = find_folder(service, month_folder_name, PARENT_FOLDER_ID)

    if not month_folder:
        month_folder_id = create_folder(service, month_folder_name, PARENT_FOLDER_ID)
    else:
        month_folder_id = month_folder["id"]
        print(f"📁 フォルダ存在済み: {month_folder_name}")
    
    weekdays = get_weekdays(year, month)
    for day in weekdays:
        folder_name = day
        if not find_folder(service, folder_name, month_folder_id):
            create_folder(service, folder_name, month_folder_id)
        else:
            print(f"📁 サブフォルダ存在済み: {folder_name}")

if __name__ == "__main__":
    main()
