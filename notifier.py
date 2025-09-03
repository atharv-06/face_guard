# Simple email notifier placeholder. Fill with real credentials if you want.
import smtplib
from email.message import EmailMessage

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'your_email@gmail.com'  # <-- change
SMTP_PASS = 'your_app_password'     # <-- change (use app password)
WARDEN_EMAIL = 'warden@example.com' # <-- change

def send_email(subject, body, attachments=None):
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = WARDEN_EMAIL
        msg.set_content(body)

        # Attach files
        if attachments:
            for path in attachments:
                with open(path, 'rb') as f:
                    data = f.read()
                    name = path.split('/')[-1]
                    msg.add_attachment(data, maintype='image',
                                       subtype='jpeg', filename=name)

        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print('Email sent successfully ✅')
    except Exception as e:
        print('Failed to send email ❌:', e)

# You can later add SMS (Twilio) or push notifications here.
