import openai
import fitz  
import docx
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text(file_id, mime_type):
    request = drive.files().get_media(fileId=file_id)
    file_path = f"tempfile.{mime_type.split('.')[-1]}"
    with open(file_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

    if 'pdf' in mime_type:
        doc = fitz.open(file_path)
        return "\n".join(page.get_text() for page in doc)
    elif 'document' in mime_type:
        d = docx.Document(file_path)
        return "\n".join([p.text for p in d.paragraphs])
    elif 'text' in mime_type:
        with open(file_path, 'r') as f:
            return f.read()
    else:
        return ""

def summarize_text(text):
    try:
        prompt = f"Summarize the following content:\n\n{text[:4000]}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f" An error occurred while summarize text : {str(e)}"
    
def summarize_folder(folder_name):
    results = drive.files().list(q=f"name contains '{folder_name}' and trashed = false", fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])
    if not files:
        return "No files to summarize."

    summaries = []
    for f in files:
        content = extract_text(f['id'], f['mimeType'])
        if content:
            summary = summarize_text(content)
            summaries.append(f"📄 {f['name']}:\n{summary}")
        else:
            summaries.append(f"⚠️ {f['name']}: Unsupported format")

    return "\n\n".join(summaries)

