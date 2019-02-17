__all__ = ['MailAccessor']

from email.message import Message
import smtplib
from helpers import Environment
# import config


class MailAccessor(object):
    def __init__(self):
        self.server = smtplib.SMTP_SSL(
            Environment().email_server,
            Environment().mail_port
        )
        self.server.login(
            Environment().mail_username,
            Environment().mail_password
        )

    def send_mail(self, recipient, payload, subject=None):
        msg = Message()
        msg['Subject'] = subject
        msg['From'] = Environment().mail_username
        msg['To'] = recipient
        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(payload)
        self.server.sendmail(
            Environment().mail_username,
            recipient,
            msg.as_string()
        )

    def quit(self):
        self.server.quit()
