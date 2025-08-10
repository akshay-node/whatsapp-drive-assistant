import os
import docx
import fitz  
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

import io

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
    
def delete_file(folder_name, file_name):
    try:
        folder_id = find_folder_id_by_name(folder_name)
        if not folder_id:
            return "Folder not found"
        file_name = file_name.strip('"').strip("'")
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        files = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute().get('files', [])
        if not files:
            return "File not found in specified folder"
        file_id = files[0]['id']
        service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        return "File deleted successfully"
    except Exception as e:
        return f"An error occurred while deleting: {str(e)}"
    
def find_folder_id_by_name(folder_name):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    response = service.files().list(
        q=query,
        fields="files(id, name)",
        corpora='user',
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        pageSize=10
    ).execute()
    folders = response.get('files', [])
    if not folders:
        print(f"No folder found with name: '{folder_name}'")
        return None
    for f in folders:
        print(f"Found folder: {f['name']} with ID: {f['id']}")
    return folders[0]['id']


def move_file(source_folder_name, file_name, dest_folder_name):
    source_folder_id = find_folder_id_by_name(source_folder_name)
    if not source_folder_id:
        return "Source folder not found"

    dest_folder_id = find_folder_id_by_name(dest_folder_name)
    if not dest_folder_id:
        return "Destination folder not found"

    file_name = file_name.strip('"').strip("'")

    query = f"name='{file_name}' and '{source_folder_id}' in parents and trashed=false"
    files = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute().get('files', [])

    if not files:
        return "File not found in source folder"
    file_id = files[0]['id']


    file = service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))

    service.files().update(fileId=file_id, addParents=dest_folder_id, removeParents=previous_parents).execute()


    return "File moved successfully"



def summarize_folder(folder_name):
    try:
        q = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        folders = service.files().list(q=q, fields="files(id, name)").execute().get('files', [])
        if not folders:
            return "Folder not found"
        folder_id = folders[0]['id']

        q_files = f"'{folder_id}' in parents and trashed=false"
        files = service.files().list(q=q_files, fields="files(id, name, mimeType)").execute().get('files', [])

        summaries = []
        for f in files:
            if f['mimeType'] in ['text/plain', 'application/vnd.google-apps.document']:
                # File content get karo
                if f['mimeType'] == 'text/plain':
                    request = service.files().get_media(fileId=f['id'])
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                    content = fh.getvalue().decode('utf-8')

                elif f['mimeType'] == 'application/vnd.google-apps.document':
                    content = service.files().export(fileId=f['id'], mimeType='text/plain').execute().decode('utf-8')

                summary = simple_summarize(content)
                summaries.append(f"{f['name']}:\n{summary}")

        if summaries:
            return "\n\n".join(summaries)
        else:
            return "No readable files found in folder."

    except Exception as e:
        return f"Error while summarizing folder: {str(e)}"


def simple_summarize(text, max_lines=3):
    lines = text.strip().split('\n')
    summary = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        summary += "\n..."
    return summary
