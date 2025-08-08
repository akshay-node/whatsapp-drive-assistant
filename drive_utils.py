import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from gpt_utils import summarize_text

load_dotenv()

creds = service_account.Credentials.from_service_account_file(
    os.getenv("GOOGLE_CREDENTIALS_JSON"),
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=creds)

def list_all_folders():
    try:
        print("[DEBUG] Starting folder listing...")
        folders = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
            supportsAllDrives=True,
    includeItemsFromAllDrives=True
        ).execute().get('files', [])
        # print("[DEBUG] Raw folder response:", folders)
        if not folders:
            print("[DEBUG] No folders found.")
            return " No folders found in your Drive."
        result = "📂 Available Folders:\n" + "\n".join(f"{f['name']}" for f in folders)
        print("[DEBUG] Final result to return:", result)
        return result
    except Exception as e:
        print("[ERROR] Exception occurred in list_all_folders:", str(e))
        return "Error occurred while listing folders."

def list_files(folder_name):
    try:
        q = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        folders = service.files().list(q=q).execute().get('files', [])
        if not folders: return "Folder nohhhht found"
        folder_id = folders[0]['id']
        files = service.files().list(q=f"'{folder_id}' in parents").execute().get('files', [])
        return "\n".join(f['name'] for f in files) if files else "No files"
    except Exception as e:
        return f" An error occurred while list files : {str(e)}"
    
def delete_file(path):
    try:
        q = f"name='{path.split('/')[-1]}'"
        files = service.files().list(q=q).execute().get('files', [])
        if not files: return "File not found"
        service.files().delete(fileId=files[0]['id']).execute()
        return "File deleted"
    except Exception as e:
        return f" An error occurred while deleting: {str(e)}"
    
def move_file(source, dest):
    try:
        q = f"name='{source.split('/')[-1]}'"
        files = service.files().list(q=q).execute().get('files', [])
        if not files: return "Source file not found"
        source_id = files[0]['id']
        q2 = f"name='{dest}' and mimeType='application/vnd.google-apps.folder'"
        folders = service.files().list(q=q2).execute().get('files', [])
        if not folders: return "Destination folder not found"
        folder_id = folders[0]['id']
        file = service.files().get(fileId=source_id, fields='parents').execute()
        prev_parents = ",".join(file.get('parents'))
        service.files().update(fileId=source_id, addParents=folder_id, removeParents=prev_parents).execute()
        return "File moved"
    except Exception as e:
        return f" An error occurred while move: {str(e)}"
    
def summarize_folder(folder_name):
    try:
        q = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        folders = service.files().list(q=q).execute().get('files', [])
        if not folders: return "Folder not found"
        folder_id = folders[0]['id']
        files = service.files().list(q=f"'{folder_id}' in parents").execute().get('files', [])
        summaries = []
        for f in files:
            if f['mimeType'] in ['text/plain', 'application/vnd.google-apps.document']:
                content = service.files().get_media(fileId=f['id']).execute().decode()
                summary = summarize_text(content)
                summaries.append(f"{f['name']}:\n{summary}")
        return "\n\n".join(summaries) if summaries else "No readable files"
    except Exception as e:
        return f" An error occurred while summarize : {str(e)}"
    