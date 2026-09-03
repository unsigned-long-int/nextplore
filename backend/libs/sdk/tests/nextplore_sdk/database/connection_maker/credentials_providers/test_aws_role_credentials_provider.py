import os
import types
import unittest
from unittest.mock import MagicMock, patch

from nextplore_sdk.database.connection_maker.credentials_providers.aws_role_credentials_provider import (
    AWSRoleCredentialsProvider,
)


class TestAWSRoleCredentialsProvider(unittest.TestCase):
    def setUp(self):
        self.profile = types.SimpleNamespace(
            region="eu-central-1",
            tenant_id="tenant123",
            database="database123",
            aws_role_arn="arn:aws:iam::999999999999:role/TenantExecutionRole",
            aws_external_id="external-abc",
            host="postgres.cluster-xyz.eu-central-1.rds.amazonaws.com",
            port=5432,
            username="db_user",
        )
        self.provider = AWSRoleCredentialsProvider.__new__(AWSRoleCredentialsProvider)
        self.provider.profile = self.profile

    @patch.dict(
        os.environ,
        {"AWS_ROLE_ARN": "arn:aws:iam::123456789012:role/BootstrapRole"},
        clear=False,
    )
    @patch("uuid.uuid4")
    @patch("boto3.Session")
    def test_assumes_role(self, session_cls_mock, uuid4_mock):
        fake_uuid = types.SimpleNamespace(hex="cafebabe01234567")
        uuid4_mock.return_value = fake_uuid

        base_session = MagicMock(name="base_session")
        sts1 = MagicMock(name="sts_client_1")
        sts1.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIA_BOOT",
                "SecretAccessKey": "SEC_BOOT",
                "SessionToken": "TOK_BOOT",
            }
        }
        base_session.client.return_value = sts1

        tenant_session = MagicMock(name="tenant_session")
        sts2 = MagicMock(name="sts_client_2")
        final_creds = {
            "AccessKeyId": "AKIA_TENANT",
            "SecretAccessKey": "SEC_TENANT",
            "SessionToken": "TOK_TENANT",
        }
        sts2.assume_role.return_value = {"Credentials": final_creds}
        tenant_session.client.return_value = sts2

        session_cls_mock.side_effect = [base_session, tenant_session]

        creds = self.provider._assume()

        self.assertEqual(creds, final_creds)

        session_cls_mock.assert_any_call()
        base_session.client.assert_called_once_with(
            "sts", region_name=self.profile.region
        )
        sts1.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::123456789012:role/BootstrapRole",
            RoleSessionName="nextplore-iam-auth-hop",
        )

        session_cls_mock.assert_called_with(
            aws_access_key_id="AKIA_BOOT",
            aws_secret_access_key="SEC_BOOT",
            aws_session_token="TOK_BOOT",
            region_name=self.profile.region,
        )

        expected_name = f"nextplore-{self.profile.database}"
        tenant_session.client.assert_called_once_with(
            "sts", region_name=self.profile.region
        )
        sts2.assume_role.assert_called_once_with(
            RoleArn=self.profile.aws_role_arn,
            RoleSessionName=expected_name,
            ExternalId=self.profile.aws_external_id,
        )

    @patch("boto3.client")
    def test_retrieves_token(self, boto3_client_mock):
        rds_client = MagicMock(name="rds_client")
        rds_client.generate_db_auth_token.return_value = "dbtoken-123"
        boto3_client_mock.return_value = rds_client

        in_creds = {
            "AccessKeyId": "AKIA_TENANT",
            "SecretAccessKey": "SEC_TENANT",
            "SessionToken": "TOK_TENANT",
        }

        token = self.provider._token(in_creds)

        self.assertEqual(token, "dbtoken-123")
        boto3_client_mock.assert_called_once_with(
            "rds",
            region_name=self.profile.region,
            aws_access_key_id="AKIA_TENANT",
            aws_secret_access_key="SEC_TENANT",
            aws_session_token="TOK_TENANT",
        )
        rds_client.generate_db_auth_token.assert_called_once_with(
            DBHostname=self.profile.host,
            Port=self.profile.port,
            DBUsername=self.profile.username,
            Region=self.profile.region,
        )

    def test_creds_composes_assume_and_token(self):
        with (
            patch.object(
                self.provider,
                "_assume",
                return_value={
                    "AccessKeyId": "X",
                    "SecretAccessKey": "Y",
                    "SessionToken": "Z",
                },
            ) as assume_mock,
            patch.object(
                self.provider, "_token", return_value="final-token"
            ) as token_mock,
        ):
            result = self.provider.creds()

        self.assertEqual(result, "final-token")
        assume_mock.assert_called_once_with()
        token_mock.assert_called_once_with(
            {"AccessKeyId": "X", "SecretAccessKey": "Y", "SessionToken": "Z"}
        )
