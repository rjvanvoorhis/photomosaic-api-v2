__all__ = ['MailAccessor']

from email.message import Message
import smtplib
import config


class MailAccessor(object):
    def __init__(self):
        self.server = smtplib.SMTP_SSL(
            config.EMAIL_SERVER,
            config.MAIL_PORT
        )
        self.server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)

    def send_mail(self, recipient, payload, subject=None):
        msg = Message()
        msg['Subject'] = subject
        msg['From'] = config.MAIL_USERNAME
        msg['To'] = recipient
        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(payload)
        self.server.sendmail(
            config.MAIL_USERNAME,
            recipient,
            msg.as_string()
        )

    def quit(self):
        self.server.quit()
