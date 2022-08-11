# Email generation and sending functionality. Requires SMTP config to be loaded.
from __future__ import absolute_import

import smtplib

from lib import config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def send_email(subject, message, attachments={}):
    smtp_config = config['smtp']

    # Prepare actual message
    body = MIMEMultipart()
    body['From'] = smtp_config['sender']
    body['To'] = smtp_config['recipient']
    body['Subject'] = subject

    body.attach(MIMEText(message))
    for attachment in attachments:
        body.attach(MIMEApplication(
            attachment['data'].read(),
            Content_Disposition='attachment; filename="%s"' % attachment['name'],
            Name=attachment['name']
        ))

    server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
    server.ehlo()
    server.starttls()
    server.login(smtp_config['user'], smtp_config['password'])
    server.sendmail(smtp_config['user'], smtp_config['recipient'], body.as_string())
    server.close()
