import requests
import urllib.parse
from django.conf import settings

def send_whatsapp_notification(message, phone=None):
    """
    Sends a WhatsApp notification using the CallMeBot API
    
    Args:
        message (str): The message you want to send
        phone (str, optional): Phone number with country code (defaults to the one configured in settings)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    # If no phone is provided, use the one from settings
    if phone is None:
        # Make sure to add WHATSAPP_PHONE in settings.py
        phone = getattr(settings, 'WHATSAPP_PHONE', None)
        if not phone:
            return False
    
    # API key for CallMeBot (add in settings.py)
    api_key = getattr(settings, 'CALLMEBOT_API_KEY', None)
    if not api_key:
        return False
    
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    # CallMeBot API URL
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey={api_key}"
    
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False 