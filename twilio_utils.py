import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from flask import request

load_dotenv()

def verify_twilio(req):
    try:
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        # print("[DEBUG] Auth Token from .env:", auth_token)
        validator = RequestValidator(auth_token)
        url = req.url
        post_vars = req.form.to_dict()
        signature = req.headers.get('X-Twilio-Signature', '')
        return validator.validate(url, post_vars, signature)
    except Exception as e:
        return f" An error occurred while verify : {str(e)}"
    
def send_whatsapp_message(to, message):
    try:
        client = Client()
        client.messages.create(
            body=message,
            from_='whatsapp:+14155238886',
            to=to
        )
    except Exception as e:
        return f" An error occurred while send whatsapp msg: {str(e)}"
    