import logging
import os
import unittest
from unittest.mock import patch, MagicMock
import sys
from twilio_receiver import TwilioReceiver
import urllib

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
root_logger.addHandler(handler)
env = {
    'REQUEST_URL': 'https://example.com/messages/post',
    'ADMIN_NUMBERS': '+187654321,+187654322',
    'TWILIO_NUMBER': '123456789',
    'TWILIO_ACCOUNT_SID': '18447389',
    'TWILIO_AUTH_TOKEN': '42030940t388jgj0s0'
}
valid_twilio_event = {
    u'Body': u'Startup',
    u'From': u'%2B187654321',
    u'FromCountry': u'US',
    u'FromState': u'PA',
    u'NumMedia': u'0',
    u'NumSegments': u'1',
    u'SmsSid': u'SM32ca848ca8f8a8d84838af8',
    u'To': u'%2B' + env.get('TWILIO_NUMBER'),
    u'ToCity': u'FORT+WASHINGTON',
    u'ToCountry': u'US',
    u'ToState': u'PA',
    u'ToZip': u'19034',
    u'twilioSignature': u'supersecretkey',
}
valid_twilio_params = {
    k: urllib.parse.unquote_plus(v) for k, v in valid_twilio_event.items() if k != u'twilioSignature'
}

class TwilioReceiverTestCase(unittest.TestCase):
    def create_patch(self, name):
        patcher = patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def patch_environ(self, env):
        patcher = patch.dict('os.environ', env)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def setUp(self):
        self.patch_environ(env)
        self.subject = TwilioReceiver(valid_twilio_event, root_logger)
        self.subject.client = MagicMock()
        self.subject.validator = MagicMock()

    def test_twilio_client_setup(self):
        with patch('twilio_receiver.Client') as mock_twilio_client_init:
            TwilioReceiver({}, root_logger)
            mock_twilio_client_init.assert_called_with(env.get('TWILIO_ACCOUNT_SID'),
                    env.get('TWILIO_AUTH_TOKEN'))

    def test_admin_number_setup(self):
        valid_admin_numbers = [x.encode('utf8') for x in env['ADMIN_NUMBERS'].split(',')]
        self.assertEqual(self.subject.admin_numbers, valid_admin_numbers)

    def test_twilio_event_parsed_correctly(self):
        self.assertEqual(self.subject.twilio_signature, valid_twilio_event[u'twilioSignature'])
        self.assertEqual(self.subject.event['Body'], valid_twilio_event[u'Body'])
        self.assertEqual(self.subject.event['To'], f'+{env.get("TWILIO_NUMBER")}')
        self.assertEqual(self.subject.event['From'], f'+187654321')
        self.assertEqual(self.subject.event.get('twilioSignature'), None)

    def test_twilio_event_parse_failure(self):
        self.assertEqual(TwilioReceiver({}, root_logger).event, {})

    def test_validate_inits_validator(self):
        with patch('twilio_receiver.RequestValidator') as mock_twilio_request_validator:
            TwilioReceiver({}, root_logger)
            mock_twilio_request_validator.assert_called_with(env.get('TWILIO_AUTH_TOKEN'))

    def test_validate_success(self):
        self.subject.validator.validate.return_value = True
        self.assertEqual(self.subject.validate(), True)
        self.subject.validator.validate.assert_called_with(
            env.get('REQUEST_URL'),
            valid_twilio_params,
            valid_twilio_event[u'twilioSignature'])

    def test_validate_invalid_request(self):
        self.subject.validator.validate.return_value = False
        self.assertEqual(self.subject.validate(), False)

    def test_validate_non_admin_sender(self):
        valid_twilio_event[u'From'] = '+19999999'
        self.subject = TwilioReceiver(valid_twilio_event, root_logger)
        self.subject.client = MagicMock()
        self.subject.validator = MagicMock()
        self.subject.validator.validate.return_value = True
        self.assertEqual(self.subject.validate(), False)
        valid_twilio_event[u'From'] = u'%2B187654321'

    def test_message(self):
        valid_twilio_event[u'Body'] = 'bayorang baby'
        self.subject = TwilioReceiver(valid_twilio_event, root_logger)
        self.assertEqual(self.subject.message(), 'bayorang baby')
        valid_twilio_event[u'Body'] = 'Startup'

    def test_ip(self):
        valid_twilio_event[u'Body'] = 'whitelist add 1.2.3.4 as example'
        self.subject = TwilioReceiver(valid_twilio_event, root_logger)
        self.assertEqual(self.subject.ip(), '1.2.3.4')
        valid_twilio_event[u'Body'] = 'Startup'

    def test_ip_description(self):
        valid_twilio_event[u'Body'] = 'whitelist add 1.2.3.4 as example'
        self.subject = TwilioReceiver(valid_twilio_event, root_logger)
        self.assertEqual(self.subject.ip_description(), 'example')
        valid_twilio_event[u'Body'] = 'Startup'

    def test_sender(self):
        self.assertEqual(self.subject.sender(),
                urllib.parse.unquote_plus(valid_twilio_event[u'From']))

    def test_send_sms(self):
        number = '987654321'
        message = 'Bingo! Unity.'

        self.subject.send_sms(number, message)
        self.subject.client.messages.create.assert_called_with(
                body=message,
                from_=self.subject.twilio_number,
                to=number)
