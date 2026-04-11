import logging
import requests
import urllib.parse
from datetime import date, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

import dns.resolver
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone as dj_timezone

logger = logging.getLogger(__name__)

_BOGOTA_TZ = ZoneInfo('America/Bogota')


def now_bogota() -> datetime:
    """Return the current `datetime` in America/Bogota (UTC-5, no DST)."""
    return dj_timezone.now().astimezone(_BOGOTA_TZ)


def today_bogota() -> date:
    """Return today's calendar date in America/Bogota."""
    return now_bogota().date()


def to_bogota_date(dt) -> date | None:
    """Convert a datetime to its Bogotá calendar date, or None if falsy."""
    if not dt:
        return None
    if dj_timezone.is_naive(dt):
        dt = dj_timezone.make_aware(dt)
    return dt.astimezone(_BOGOTA_TZ).date()

_SPANISH_MONTHS = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre',
}


_dns_resolver = dns.resolver.Resolver()
_dns_resolver.lifetime = 2.0


@lru_cache(maxsize=256)
def check_domain_mx(domain):
    """Return True if *domain* has MX (non-null) or A records.

    Detects RFC 7505 null MX (exchange=".") as invalid.
    Fails open on timeout so a slow nameserver doesn't block the caller.
    """
    try:
        mx_records = _dns_resolver.resolve(domain, 'MX')
        for rdata in mx_records:
            if str(rdata.exchange).rstrip('.') == '':
                return False
        return True
    except dns.exception.Timeout:
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers):
        pass
    try:
        _dns_resolver.resolve(domain, 'A')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers, dns.exception.Timeout):
        pass
    return False


def validate_email_domain_mx(email):
    """Return True if the email domain can receive mail (has MX or A records).

    Returns True on empty/blank input so optional fields pass through.
    """
    if not email or '@' not in email:
        return True
    domain = email.rsplit('@', 1)[1].lower().strip()
    if not domain:
        return True
    try:
        return check_domain_mx(domain)
    except Exception:
        logger.warning('DNS lookup failed for domain %s, allowing email', domain)
        return True


def format_cop_email(value):
    """Format a number for COP email display: 1'490.000

    Uses dot as thousands separator and apostrophe as millions separator.
    Truncates to integer (COP values have no meaningful cents).
    Examples: 1490000 → "1'490.000", 123456 → "123.456", 5000 → "5.000"
    """
    if value is None:
        return ''
    try:
        cleaned = str(value).replace(',', '')
        num = int(float(cleaned))
    except (TypeError, ValueError):
        return str(value)
    if num < 0:
        return f'-{format_cop_email(-num)}'
    formatted = f'{num:,}'
    groups = formatted.split(',')
    if len(groups) <= 2:
        return '.'.join(groups)
    return "'".join(groups[:-1]) + f'.{groups[-1]}'


def format_bogota_date(dt) -> str:
    """Return '8 de abril, 2026' in Bogotá timezone (America/Bogota).

    Accepts both datetime and date instances. Plain date instances are
    formatted directly (no timezone conversion needed).
    """
    if not dt:
        return ''
    if isinstance(dt, datetime):
        if dj_timezone.is_naive(dt):
            dt = dj_timezone.make_aware(dt)
        dt = dt.astimezone(_BOGOTA_TZ)
    elif not isinstance(dt, date):
        return ''
    return f'{dt.day} de {_SPANISH_MONTHS[dt.month]}, {dt.year}'


def format_bogota_datetime(dt) -> str:
    """Return '8 de abril, 2026 — 14:30' in Bogotá timezone (America/Bogota)."""
    if not dt:
        return ''
    if dj_timezone.is_naive(dt):
        dt = dj_timezone.make_aware(dt)
    bogota = dt.astimezone(_BOGOTA_TZ)
    return (
        f'{bogota.day} de {_SPANISH_MONTHS[bogota.month]}, {bogota.year}'
        f' — {bogota.strftime("%H:%M")}'
    )

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