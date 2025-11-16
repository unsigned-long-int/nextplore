import os
import boto3
from typing import Dict, Any

from .credentials_provider import CredentialsProvider


class AWSRoleCredentialsProvider(CredentialsProvider):
    def _assume(self) -> Dict[str, Any]:
        base_session = boto3.Session()
        sts = base_session.client('sts', region_name=self.profile.region)
        creds = sts.assume_role(
            RoleArn=os.getenv('AWS_ROLE_ARN'),
            RoleSessionName='nextplore-iam-auth-hop'
        )['Credentials']
        tenant = boto3.Session(
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken'],
            region_name=self.profile.region
        )

        role_session_name = f'nextplore-{self.profile.database}'
        sts = tenant.client('sts', region_name=self.profile.region)
        creds = sts.assume_role(
            RoleArn=self.profile.aws_role_arn,
            RoleSessionName=role_session_name,
            ExternalId=self.profile.aws_external_id
        )['Credentials']
        return creds
    
    def _token(self, creds: Dict[str, Any]) -> str:
        rds = boto3.client(
            'rds', 
            region_name=self.profile.region,
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
        )
        token = rds.generate_db_auth_token(
            DBHostname=self.profile.host, 
            Port=self.profile.port, 
            DBUsername=self.profile.username, 
            Region=self.profile.region
        )
        return token
    
    def creds(self, **_: Any) -> str:
        creds = self._assume()
        return self._token(creds)
