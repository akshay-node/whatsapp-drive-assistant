from flask import Flask, request
from twilio_utils import verify_twilio, send_whatsapp_message
from drive_utils import list_files, delete_file, move_file, summarize_folder
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
    if msg.startswith('LIST'):
        folder = msg[5:]
        result = list_files(folder)
        send_whatsapp_message(sender, result)
    elif msg.startswith('DELETE'):
        path = msg[7:]
        result = delete_file(path)
        send_whatsapp_message(sender, result)
    elif msg.startswith('MOVE'):
        parts = msg[5:].split(' ')
        if len(parts) == 2:
            result = move_file(parts[0], parts[1])
            send_whatsapp_message(sender, result)
        else:
            send_whatsapp_message(sender, 'Invalid MOVE syntax')
    elif msg.startswith('SUMMARY'):
        folder = msg[8:]
        result = summarize_folder(folder)
        send_whatsapp_message(sender, result)
    else:
        send_whatsapp_message(sender, 'Unknown command')
    return 'OK', 200

if __name__ == '__main__':
    app.run(port=5000)