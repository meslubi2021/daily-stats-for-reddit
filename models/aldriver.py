import json
import utils
import config_reader as config
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from io import BytesIO

COINS_COLLECTION = "COINS"
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'models/drv/service.json'
SNAPSHOT_FOLDER_ID = utils.get_env("SNAPSHOT_FOLDER_ID") or config.get('DB', 'SNAPSHOT_FOLDER_ID', fallback=None)

class Aldriver:

    def __init__(self, date):
        self.json_snapshot = json.loads('{}')
        self.drive_service = None
        self.creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.drive = build('drive', 'v3', credentials = self.creds)
        self.date = date.strftime("%Y%m%d")
    
    def insert_coins(self, coins_dict):
        coins = [c.__dict__ for c in coins_dict.values()]
        coins_jarr = json.dumps(coins)
        self.json_snapshot[COINS_COLLECTION] = coins_jarr
    
    def set_id_date(self, id):
        self.json_snapshot["ID"] = id
        self.json_snapshot["DATE"] = self.date
    
    def store(self):
        txt_fd = BytesIO(json.dumps(self.json_snapshot).encode())
        file_metadata = {'name': f'{self.date}.json', 'parents': [SNAPSHOT_FOLDER_ID]}
        media = MediaIoBaseUpload(txt_fd, mimetype='application/json',
            chunksize=1024*1024, resumable=True)
        file = self.drive.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
        print('Uploaded File with ID: %s' % file.get('id'))
        txt_fd.close()
    