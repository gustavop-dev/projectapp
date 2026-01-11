import requests
import urllib.parse
from django.conf import settings
from django.core.mail import send_mail

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
            print("❌ WhatsApp notification failed: WHATSAPP_PHONE not configured")
            return False
    
    # API key for CallMeBot (add in settings.py)
    api_key = getattr(settings, 'CALLMEBOT_API_KEY', None)
    if not api_key:
        print("❌ WhatsApp notification failed: CALLMEBOT_API_KEY not configured")
        return False
    
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    # CallMeBot API URL
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey={api_key}"
    
    try:
        print(f"📱 Sending WhatsApp notification to {phone}...")
        response = requests.get(url)
        
        if response.status_code == 200:
            print(f"✅ WhatsApp notification sent successfully!")
            return True
        else:
            print(f"❌ WhatsApp notification failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending WhatsApp notification: {e}")
        return False

def send_email_notification(subject, message, recipient_email=None):
    """
    Sends an email notification
    
    Args:
        subject (str): Email subject
        message (str): Email message body
        recipient_email (str, optional): Recipient email (defaults to the one configured in settings)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if recipient_email is None:
        recipient_email = getattr(settings, 'NOTIFICATION_EMAIL', None)
        if not recipient_email:
            print("❌ Email notification failed: NOTIFICATION_EMAIL not configured")
            return False
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if not from_email:
        print("❌ Email notification failed: DEFAULT_FROM_EMAIL not configured")
        return False
    
    try:
        print(f"📧 Sending email notification to {recipient_email}...")
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        print(f"✅ Email notification sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Error sending email notification: {e}")
        return False 