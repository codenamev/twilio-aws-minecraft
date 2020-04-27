from __future__ import print_function

import boto3
import logging
import os
import socket
from botocore.exceptions import ClientError

class Ec2Manager:

    def __init__(self, logger=logging.getLogger(__name__)):
        self.ec2 = boto3.client('ec2')
        self.instance_id = os.environ.get('EC2_INSTANCE_ID')
        self.security_group_id = os.environ.get('EC2_SECURITY_GROUP_ID')
        self.logger = logger

    def get_host_ip(self):
        try:
            host_name = socket.gethostname()
            host_ip = socket.gethostbyname(host_name)
            self.logger.debug(f'Hostname: {host_name}')
            self.logger.debug(f'IP: {host_ip}')
            return host_ip
        except:
            self.logger.warning("Unable to get Hostname and IP")
            return None

    def instance_status(self):
        try:
            response = self.ec2.describe_instance_status(
                    InstanceIds=[self.instance_id],
                    DryRun=False
                    )
            self.logger.debug(f'EC2 Status: {response}')
            return response['InstanceStatuses'][0]['InstanceState']['Name']
        except IndexError as error:
            return 'Unknown'
        except ClientError as error:
            self.logger.debug(f'[{__name__}#instance_status] EC2 Error: {error}')
            return 'Unknown'

    def start_instance(self):
        try:
            ec2_resp = self.ec2.start_instances(InstanceIds=[self.instance_id])
            self.logger.debug(f'EC2 Response: {ec2_resp}')
            return True
        except ClientError as error:
            self.logger.debug(f'[{__name__}#start_instance] EC2 Error: {error.response}')
            return False

    def stop_instance(self):
        try:
            ec2_resp = self.ec2.stop_instances(InstanceIds=[self.instance_id])
            self.logger.debug(f'EC2 Response: {ec2_resp}')
            return True
        except ClientError as error:
            self.logger.debug(f'[{__name__}#stop_instance] EC2 Error: {error.response}')
            return False

    def ingress_permissions_for_ip(self, ip, port, description):
        return [
                {
                    'FromPort': int(port),
                    'ToPort': int(port),
                    'IpProtocol': 'TCP',
                    'IpRanges': [
                        {
                            'CidrIp': ip,
                            'Description': description,
                        },
                    ],
                },
                {
                    'FromPort': int(port),
                    'ToPort': int(port),
                    'IpProtocol': 'UDP',
                    'IpRanges': [
                        {
                            'CidrIp': ip,
                            'Description': description,
                        },
                    ],
                },
            ]

    def add_ip_to_whitelist(self, ip, port=80, description=''):
        try:
            ec2_resp = self.ec2.authorize_security_group_ingress(
                    DryRun=False,
                    GroupId=self.security_group_id,
                    IpPermissions=self.ingress_permissions_for_ip(f'{ip}/32', port, description)
            )
            self.logger.debug(f'EC2 Response: {ec2_resp}')
            return True
        except ClientError as error:
            if 'already exists' in error.response['Error']['Message']:
                return True
            else:
                self.logger.debug(f'[{__name__}#add_ip_to_whitelist] EC2 Error: {error.response}')
                return False

    def remove_ip_from_whitelist(self, ip, port=80, description=''):
        try:
            ec2_resp = self.ec2.revoke_security_group_ingress(
                    DryRun=False,
                    GroupId=self.security_group_id,
                    IpPermissions=self.ingress_permissions_for_ip(f'{ip}/32', port, description)
            )
            self.logger.debug(f'EC2 Response: {ec2_resp}')
            return True
        except ClientError as error:
            self.logger.debug(f'[{__name__}#remove_ip_from_whitelist] EC2 Error: {error.response}')
            return False
