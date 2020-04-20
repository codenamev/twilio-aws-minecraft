import unittest
import twilio_function
from twilio_receiver import TwilioReceiver
from unittest.mock import patch, MagicMock, ANY

env = {
    'REQUEST_URL': 'https://example.com/messages/post',
    'ADMIN_NUMBERS': '+187654321,+187654322',
    'MINECRAFT_HOST': '1.2.3.4',
    'MINECRAFT_PORT': '5565',
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

class TwilioFunctionTestCase(unittest.TestCase):
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
        self.twilio_event = valid_twilio_event
        self.mock_twilio_receiver = self.create_patch('twilio_function.TwilioReceiver')
        self.mock_ec2 = self.create_patch('twilio_function.Ec2Manager')

    def test_invalid_twilio_event(self):
        self.mock_twilio_receiver.return_value.validate.return_value = False;
        twilio_function.lambda_handler(self.twilio_event, {})
        self.mock_twilio_receiver.assert_called_with(self.twilio_event, ANY)
