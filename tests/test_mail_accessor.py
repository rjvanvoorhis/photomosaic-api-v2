import unittest
from ddt import data, ddt
from accessors import mail_accessor
from tests.utilities import BaseTest


def make_response(payload, subject=None):
    subject = subject if subject is not None else ''
    resp = f'Subject: {subject}\nFrom: my_username\nTo: recipient\nContent-Type: text/html\n\n{payload}'
    return resp


@ddt
class MailAccessorTest(BaseTest):
    import_route = 'accessors.mail_accessor'

    def setUp(self):
        self.mock_env = self.add_patcher('Environment').return_value
        self.mock_env.mail_username = 'my_username'
        self.mock_env.mail_password = 'my_pswd'
        self.mock_env.mail_port = 465
        self.mock_env.email_server = 'mail_server'
        self.mock_smtplib = self.add_patcher('smtplib')
        self.mock_server = self.mock_smtplib.SMTP_SSL.return_value

    def test_init(self):
        mail_accessor.MailAccessor()
        self.mock_smtplib.SMTP_SSL.assert_called_with(
          'mail_server', 465
        )
        self.mock_server.login.assert_called_with(
            'my_username', 'my_pswd'
        )

    @data(
        None,
        'New User'
    )
    def test_send_mail(self, subject):
        mail = mail_accessor.MailAccessor()
        mail.send_mail('recipient', 'payload', subject=subject)
        mail.quit()
        self.mock_server.sendmail.assert_called_with(
            'my_username',
            'recipient',
            make_response('payload', subject)
        )
        self.mock_server.quit.assert_called_once()


if __name__ == '__main__':
    unittest.main()


