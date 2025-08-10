from flask import Flask, request , Response
from twilio_utils import verify_twilio, send_whatsapp_message
from drive_utils import list_files,list_all_folders, delete_file, move_file, summarize_folder
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


@app.route('/webhook', methods=['POST'])
def webhook():
    if not verify_twilio(request): return "Invalid", 403
    msg = request.form.get('Body', '').strip()
    sender = request.form.get('From', '')
    if msg.upper().strip() == "LISTALL":
        result = list_all_folders()
        send_whatsapp_message(sender, result)
    elif msg.startswith('LIST'):
        folder = msg[5:]
        result = list_files(folder)
        send_whatsapp_message(sender, result)
    elif msg.startswith('DELETE'):
        parts = msg.split(' ', 2)  
        if len(parts) == 3:
            folder_name = parts[1]
            file_name = parts[2]
            result = delete_file(folder_name, file_name) 
        else:
            result = "Invalid DELETE command format. Use: DELETE FOLDERNAME FILENAME"
        send_whatsapp_message(sender, result)
    elif msg.upper().startswith('MOVE'):
        command_args = msg[5:].strip()
        parts = command_args.split(maxsplit=2)  
        if len(parts) == 3:
            source_folder = parts[0]
            file_name = parts[1]
            dest_folder = parts[2]
            result = move_file(source_folder, file_name, dest_folder)
            send_whatsapp_message(sender, result)
        else:
            send_whatsapp_message(sender, 'Invalid MOVE syntax. Use: MOVE <source_folder> <file_name> <dest_folder>')
    elif msg.startswith('SUMMARY'):
        folder = msg[8:]
        result = summarize_folder(folder)
        send_whatsapp_message(sender, result)
    else:
        send_whatsapp_message(sender, 'Unknown command')
    return 'OK', 200

if __name__ == '__main__':
    app.run(port=5000)