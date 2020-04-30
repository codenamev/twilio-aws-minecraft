import sys

sys.path.append('./package')

import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import logging
import os
import socket
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from twilio_receiver import TwilioReceiver
import urllib

from ec2_manager import Ec2Manager

def lambda_handler(event, context):
    resp = MessagingResponse()
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)

    incoming_twilio = TwilioReceiver(event, root_logger)
    twilio_response = MessagingResponse()

    print("Received event: " + str(event))
    print(f'Form params: {incoming_twilio.event}')

    if not incoming_twilio.validate():
        twilio_response.message("I'm sorry, but I can't help you.")
        return str(twilio_response)
    else:
        ec2_manager = Ec2Manager(root_logger)
        minecraft_host = os.environ['MINECRAFT_HOST']
        minecraft_port = os.environ['MINECRAFT_PORT']

        if incoming_twilio.message() == 'status':
            if ec2_manager.instance_status() == 'running':
                twilio_response.message('Minecraft server online: %s on port %d:' % (minecraft_host, int(minecraft_port)))
            else:
                twilio_response.message('Server instance is not running. Text "startup" to get it running.')
        elif incoming_twilio.message() == 'startup':
            incoming_twilio.send_sms(incoming_twilio.sender(), 'Starting Minecraft server...')
            if ec2_manager.start_instance():
                twilio_response.message(f'Minecraft server started at {minecraft_host}. Give it a minute to warm up :-)')
            else:
                twilio_response.message("Unable to start the server at this time.")
        elif incoming_twilio.message() == 'shutdown':
            incoming_twilio.send_sms(incoming_twilio.sender(), 'Stopping Minecraft server...')
            if ec2_manager.stop_instance():
                twilio_response.message('Minecraft server shutting down.')
            else:
                twilio_response.message("Unable to shutdown the server at this time.")
        elif incoming_twilio.message().startswith('whitelist add '):
            if len(incoming_twilio.ip()) > 0:
                ec2_manager.add_ip_to_whitelist(incoming_twilio.ip(),
                        minecraft_port,
                        incoming_twilio.ip_description())
                twilio_response.message(f'Added {incoming_twilio.ip()} to whitelist as "{incoming_twilio.ip_description()}"')
            else:
                twilio_response.message("usage: whitelist add 123.456.78.9 as person's home")
        elif incoming_twilio.message().startswith('whitelist remove '):
            if len(incoming_twilio.ip()) > 0:
                ec2_manager.remove_ip_from_whitelist(incoming_twilio.ip(),
                        minecraft_port,
                        incoming_twilio.ip_description())
                twilio_response.message = f'Removed {incoming_twilio.ip()} from whitelist.'
            else:
                twilio_response.message("usage: whitelist add 123.456.78.9 as person's home")
        else:
            twilio_response.message('Valid commands are: "status", "startup", "shutdown", or "whitelist"')

        return str(twilio_response)

if __name__ == "__main__":
    event = []
    context = []
    lambda_handler(event, context)
