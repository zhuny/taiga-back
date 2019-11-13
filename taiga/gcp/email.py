from typing import List

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, SafeMIMEMultipart
from django.core.mail.backends.base import BaseEmailBackend


class MailGunMailSender(BaseEmailBackend):
    def _get_message_type(self, message):
        yield from message.alternatives
        yield message.body, 'text/plain'

    def write_message(self, message: EmailMultiAlternatives):
        data = {
            "from": message.from_email,
            "to": message.to,
            "subject": message.subject
        }

        for body, content_type in self._get_message_type(message):
            if content_type == 'text/html':
                data['html'] = body
            elif content_type == 'text/plain':
                data['text'] = body
            else:
                continue
            break

        requests.post(
            settings.MAILGUN_API_URL,
            auth=("api", settings.MAILFUN_API_SECRET),
            data=data
        )

    def send_messages(self, email_messages: List[EmailMultiAlternatives]):
        for message in email_messages:
            self.write_message(message)


