import os.path
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


import google.auth
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']

#quickstartを動かした後にできたtoken.jsonを同階層にいれる
creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)


with open("token.json", "w") as token:
    token.write(creds.to_json())

    
service = build("drive", "v3", credentials=creds)

#quickstart.pyを動かした後にフォルダの固有IDを取得し、入力する
query = "'folderID' in parents"
results = service.files().list(
    q=query,
    pageSize=1000, fields="nextPageToken, files(id, name)").execute()
files = results.get('files', [])

if files:
    for file in files:
        request = service.files().get_media(fileId=file['id'])
        fh = io.FileIO(file['name'], mode='wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()