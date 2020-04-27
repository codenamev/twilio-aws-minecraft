import unittest
from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock
from ec2_manager import Ec2Manager

class Ec2ManagerTestCase(unittest.TestCase):
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
        self.create_patch('boto3.client')
        self.patch_environ({
            'MASTER_NUMBER': '123456789',
            'EC2_INSTANCE_ID': 'i-484820488',
            'EC2_SECURITY_GROUP_ID': 'sg-8484839',
            'TWILIO_ACCOUNT_SID': '18447389',
            'TWILIO_AUTH_TOKEN': '42030940t388jgj0s0'
        })
        self.subject = Ec2Manager()
        self.subject.ec2 = MagicMock()

    def test_get_host_ip(self):
        mock_hostname = self.create_patch('ec2_manager.socket.gethostname')
        mock_hostname.return_value = 'testbob.example.com'
        mock_hostbyname = self.create_patch('ec2_manager.socket.gethostbyname')
        mock_hostbyname.return_value = '1.2.3.4'

        self.assertEqual(self.subject.get_host_ip(), '1.2.3.4')

    def test_instance_status(self):
        self.subject.ec2.describe_instance_status.return_value = {
            'InstanceStatuses': [
                {
                    'InstanceState': { 'Name': 'started' },
                },
            ]
        }

        self.assertEqual(self.subject.instance_status(), 'started')
        self.subject.ec2.describe_instance_status.assert_called_with(
                InstanceIds=['i-484820488'],
                DryRun=False)

    def test_instance_status_without_state(self):
        self.subject.ec2.describe_instance_status.return_value = {
            'InstanceStatuses': []
        }

        self.assertEqual(self.subject.instance_status(), 'Unknown')

    def test_instance_status_with_client_error(self):
        self.subject.ec2.describe_instance_status.side_effect = ClientError(MagicMock(), 'describe_instance_status')
        self.assertEqual(self.subject.instance_status(), 'Unknown')

    def test_start_instance(self):
        self.assertEqual(self.subject.start_instance(), True)
        self.subject.ec2.start_instances.assert_called_with(InstanceIds=['i-484820488'])

    def test_start_instance_with_client_error(self):
        self.subject.ec2.start_instances.side_effect = ClientError(MagicMock(), 'start_instances')
        self.assertEqual(self.subject.start_instance(), False)

    def test_stop_instance(self):
        self.assertEqual(self.subject.stop_instance(), True)
        self.subject.ec2.stop_instances.assert_called_with(InstanceIds=['i-484820488'])

    def test_stop_instance_with_client_error(self):
        self.subject.ec2.stop_instances.side_effect = ClientError(MagicMock(), 'stop_instances')
        self.assertEqual(self.subject.stop_instance(), False)

    def test_ingress_permissions_for_ip(self):
        ip = '1.2.3.4'
        port = '123'
        description = 'howdy'

        self.assertEqual(self.subject.ingress_permissions_for_ip(ip, port, description),
                [
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
                ])

    def test_add_ip_to_whitelist(self):
        ip = '1.2.3.4'
        port = '123'
        description = 'howdy'

        self.assertEqual(
                self.subject.add_ip_to_whitelist(ip, port, description),
                True)

        self.subject.ec2.authorize_security_group_ingress.assert_called_with(
                DryRun=False,
                GroupId=self.subject.security_group_id,
                IpPermissions=self.subject.ingress_permissions_for_ip(f'{ip}/32', port, description))

    def test_add_ip_to_whitelist_with_client_error(self):
        ip = '1.2.3.4'
        port = '123'
        description = 'howdy'

        self.subject.ec2.authorize_security_group_ingress.side_effect = ClientError(MagicMock(), 'authorize_security_group_ingress')

        self.assertEqual(
                self.subject.add_ip_to_whitelist(ip, port, description),
                False)

    def test_remove_ip_from_whitelist(self):
        ip = '1.2.3.4'
        port = '123'
        description = 'howdy'

        self.assertEqual(
                self.subject.remove_ip_from_whitelist(ip, port, description),
                True)

        self.subject.ec2.revoke_security_group_ingress.assert_called_with(
                DryRun=False,
                GroupId=self.subject.security_group_id,
                IpPermissions=self.subject.ingress_permissions_for_ip(f'{ip}/32', port, description))

    def test_remove_ip_from_whitelist_with_client_error(self):
        ip = '1.2.3.4'
        port = '123'
        description = 'howdy'

        self.subject.ec2.revoke_security_group_ingress.side_effect = ClientError(MagicMock(), 'authorize_security_group_ingress')

        self.assertEqual(
                self.subject.remove_ip_from_whitelist(ip, port, description),
                False)
