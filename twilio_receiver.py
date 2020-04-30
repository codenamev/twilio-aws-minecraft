import logging
import re
import os
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from twilio.request_validator import RequestValidator
import sys
import urllib

sys.path.append('./package')

class TwilioReceiver:
    def __init__(self, twilio_lambda_event = {}, logger = logging.getLogger()):
        self.client = Client(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
        self.twilio_number = os.environ.get('TWILIO_NUMBER')
        self.admin_numbers = [x.encode('utf8') for x in os.environ['ADMIN_NUMBERS'].split(',')]
        self.logger = logger
        self.event = {}
        self.twilio_signature = ''
        self.parse_event(twilio_lambda_event)
        self.validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

    def message(self):
        return self.event.get(u'Body', '')

    def sender(self):
        return self.event.get(u'From', '')

    def ip(self):
        try:
            return re.split(r'whitelist\sadd|remove\s', self.message())[-1].strip().split(' as ')[0]
        except IndexError:
            return ''

    def ip_description(self):
        try:
            return re.split(r'whitelist\sadd|remove\s', self.message())[-1].strip().split(' as ')[1]
        except IndexError:
            return ''

    def parse_event(self, event):
        try:
            self.twilio_signature = event[u'twilioSignature']
            self.event = {
                k: urllib.parse.unquote_plus(v) for k, v in event.items() if k != u'twilioSignature'
            }
        except KeyError as key_error:
            self.logger.error(f'Twilio event is missing key: {key_error}')
            self.twilio_signature = ''
            self.event = {}

    def valid_request(self):
        return self.validator.validate(
            os.environ['REQUEST_URL'],
            self.event,
            self.twilio_signature
        )

    def requester_is_an_admin(self):
        return (u'From' in self.event and self.event[u'From'].encode('utf8') in self.admin_numbers)

    def validate(self):
        return self.valid_request() and self.requester_is_an_admin()

    def send_sms(self, phone_number, message):
        twilio_message = self.client.messages.create(
                body=message,
                from_=self.twilio_number,
                to=phone_number
                )
        self.logger.info(f'Sent SMS: {message}')
        return message
