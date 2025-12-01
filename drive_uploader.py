"""
Google Drive integration for uploading FIT files.
"""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle


class DriveUploader:
    """Handles Google Drive file uploads."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    CREDENTIALS_FILE = 'credentials.json'
    TOKEN_FILE = 'token.pickle'
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self):
        """Authenticate with Google Drive API."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Credentials file '{self.CREDENTIALS_FILE}' not found. "
                        "Please download it from Google Cloud Console and place it in the project root."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        self.service = build('drive', 'v3', credentials=creds)
        return True
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """Create a folder in Google Drive."""
        if not self.service:
            self.authenticate()
        
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
    
    def find_or_create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """Find existing folder or create a new one."""
        if not self.service:
            self.authenticate()
        
        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        
        results = self.service.files().list(q=query, fields='files(id, name)').execute()
        folders = results.get('files', [])
        
        if folders:
            return folders[0]['id']
        else:
            return self.create_folder(folder_name, parent_folder_id)
    
    def upload_file(self, file_path: str, folder_id: str = None, file_name: str = None) -> str:
        """Upload a file to Google Drive."""
        if not self.service:
            self.authenticate()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_metadata = {
            'name': file_name or os.path.basename(file_path)
        }
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaFileUpload(file_path, resumable=True)
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return file.get('id'), file.get('webViewLink')
    
    def upload_fit_file(self, fit_file_path: str, folder_name: str = 'Swim FIT Files') -> tuple:
        """Upload a FIT file to Google Drive in a dedicated folder."""
        if not self.service:
            self.authenticate()
        
        # Find or create the swim files folder
        folder_id = self.find_or_create_folder(folder_name)
        
        # Upload the file
        file_id, web_link = self.upload_file(fit_file_path, folder_id)
        
        return file_id, web_link, folder_id

