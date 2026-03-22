import unittest
from uuid import uuid4, UUID

from svc_integration_contracts.models import (
    IntegrationUpdateRequest,
    IntegrationCreateRequest,
    Auth,
    DB,
    Cloud
)

from integration_service.domain.models.integration import (
    IntegrationUpdate,
    IntegrationCreate,
    IntegrationProfile,
    Integration
)
from integration_service.database.models import IntegrationORM
from integration_service.domain.mappers.integration import (
    integration_update_from_dto,
    integration_create_from_dto,
    orm_from_integration_create,
    integration_profile_from_orm,
    integration_from_orm
)


class TestIntegrationUpdateFromDTO(unittest.TestCase):

    def test_converts_all_fields(self):
        payload = IntegrationUpdateRequest(
            connection_name='test_connection',
            host='localhost',
            port=5432,
            database_name='test_db',
            autosync_on=True
        )

        result = integration_update_from_dto(payload)

        self.assertIsInstance(result, IntegrationUpdate)
        self.assertEqual(result.connection_name, 'test_connection')
        self.assertEqual(result.host, 'localhost')
        self.assertEqual(result.port, 5432)
        self.assertEqual(result.database_name, 'test_db')
        self.assertEqual(result.autosync_on, True)

    def test_handles_optional_fields(self):
        payload = IntegrationUpdateRequest(
            connection_name='test',
            host=None,
            port=None,
            database_name=None,
            autosync_on=False
        )

        result = integration_update_from_dto(payload)

        self.assertIsNone(result.host)
        self.assertIsNone(result.port)
        self.assertIsNone(result.database_name)
        self.assertFalse(result.autosync_on)


class TestIntegrationCreateFromDTO(unittest.TestCase):

    def setUp(self):
        self.tenant_id = 'tenant'
        self.client_id = 'client_id'
        self.kek_kid = 'kek_kid'

    def test_converts_all_required_fields(self):
        payload = IntegrationCreateRequest(
            auth=Auth.iam,
            cloud=Cloud.azure,
            db=DB.postgresql,
            connection_name='test_connection',
            descr='test-descr',
            host='localhost',
            database_name='test_db',
            kek_kid=self.kek_kid,
            port=5432,
            warehouse='warehouse1',
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            region='us-east-1',
            azure_cert_kid='cert_kid_123',
            azure_cert_name='test_cert',
            azure_public_key_pem='-----BEGIN PUBLIC KEY-----',
            snowflake_public_key_pem='-----BEGIN PUBLIC KEY-----',
            autosync_on=True
        )

        result = integration_create_from_dto(payload)

        self.assertIsInstance(result, IntegrationCreate)
        self.assertEqual(result.auth, Auth.iam)
        self.assertEqual(result.cloud, Cloud.azure)
        self.assertEqual(result.db, DB.postgresql)
        self.assertEqual(result.connection_name, 'test_connection')
        self.assertEqual(result.host, 'localhost')
        self.assertEqual(result.database_name, 'test_db')
        self.assertEqual(result.kek_kid, self.kek_kid)
        self.assertEqual(result.port, 5432)
        self.assertEqual(result.warehouse, 'warehouse1')
        self.assertEqual(result.tenant_id, self.tenant_id)
        self.assertEqual(result.client_id, self.client_id)
        self.assertEqual(result.region, 'us-east-1')
        self.assertEqual(result.azure_cert_kid, 'cert_kid_123')
        self.assertEqual(result.azure_cert_name, 'test_cert')
        self.assertEqual(result.azure_public_key_pem, '-----BEGIN PUBLIC KEY-----')
        self.assertEqual(result.snowflake_public_key_pem, '-----BEGIN PUBLIC KEY-----')
        self.assertTrue(result.autosync_on)

    def test_handles_minimal_payload(self):
        payload = IntegrationCreateRequest(
            auth=Auth.password_native,
            cloud=Cloud.aws,
            db=DB.mysql,
            connection_name='minimal',
            descr='test-descr',
            host='db.example.com',
            database_name='mydb',
            kek_kid=self.kek_kid,
            port=3306,
            warehouse=None,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            region=None,
            azure_cert_kid=None,
            azure_cert_name=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=False
        )

        result = integration_create_from_dto(payload)

        self.assertEqual(result.auth, Auth.password_native)
        self.assertEqual(result.connection_name, 'minimal')
        self.assertIsNone(result.warehouse)
        self.assertIsNone(result.region)
        self.assertFalse(result.autosync_on)


class TestORMFromIntegrationCreate(unittest.TestCase):

    def setUp(self):
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.tenant_id = 'tenant_id'
        self.client_id = 'client_id'
        self.kek_kid = 'kek_kid'

    def test_converts_to_orm_with_all_fields(self):
        integration_create = IntegrationCreate(
            auth=Auth.cert,
            cloud=Cloud.gcp,
            db=DB.sqlserver,
            connection_name='prod_connection',
            descr='test-descr',
            host='prod.example.com',
            database_name='prod_db',
            kek_kid=self.kek_kid,
            port=443,
            warehouse='prod_warehouse',
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            region='us-west-2',
            azure_cert_kid='cert_123',
            azure_cert_name='prod_cert',
            azure_public_key_pem='-----BEGIN PUBLIC KEY-----\nAZURE',
            snowflake_public_key_pem='-----BEGIN PUBLIC KEY-----\nSNOWFLAKE',
            autosync_on=True
        )

        result = orm_from_integration_create(
            self.organization_id,
            self.user_id,
            integration_create
        )

        self.assertIsInstance(result, IntegrationORM)
        self.assertEqual(result.organization_id, self.organization_id)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.auth, Auth.cert)
        self.assertEqual(result.cloud, Cloud.gcp)
        self.assertEqual(result.db, DB.sqlserver)
        self.assertEqual(result.connection_name, 'prod_connection')
        self.assertEqual(result.host, 'prod.example.com')
        self.assertEqual(result.port, 443)
        self.assertEqual(result.database_name, 'prod_db')
        self.assertEqual(result.warehouse, 'prod_warehouse')
        self.assertEqual(result.tenant_id, self.tenant_id)
        self.assertEqual(result.client_id, self.client_id)
        self.assertEqual(result.region, 'us-west-2')
        self.assertEqual(result.azure_cert_kid, 'cert_123')
        self.assertEqual(result.azure_cert_name, 'prod_cert')
        self.assertEqual(result.azure_public_key_pem, '-----BEGIN PUBLIC KEY-----\nAZURE')
        self.assertEqual(result.snowflake_public_key_pem, '-----BEGIN PUBLIC KEY-----\nSNOWFLAKE')
        self.assertEqual(result.kek_kid, self.kek_kid)
        self.assertTrue(result.autosync_on)

    def test_preserves_types(self):
        integration_create = IntegrationCreate(
            auth=Auth.password_proxy,
            cloud=Cloud.gcp,
            db=DB.postgresql,
            connection_name='test',
            descr='test-descr',
            host='localhost',
            database_name='test',
            kek_kid=self.kek_kid,
            port=5432,
            warehouse=None,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            region=None,
            azure_cert_kid=None,
            azure_cert_name=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=False
        )

        result = orm_from_integration_create(
            self.organization_id,
            self.user_id,
            integration_create
        )

        self.assertIsInstance(result.organization_id, UUID)
        self.assertIsInstance(result.user_id, UUID)
        self.assertIsInstance(result.tenant_id, str)
        self.assertIsInstance(result.client_id, str)
        self.assertIsInstance(result.kek_kid, str)


class TestIntegrationProfileFromORM(unittest.TestCase):

    def test_converts_orm_to_profile(self):
        integration_id = uuid4()
        integration_orm = IntegrationORM(
            id=integration_id,
            organization_id=uuid4(),
            user_id=uuid4(),
            auth=Auth.password_proxy,
            cloud=Cloud.snowflake_managed,
            db=DB.snowflake,
            connection_name='test_connection',
            database_name='test_db',
            host='test.example.com',
            port=443,
            autosync_on=True,
            warehouse='warehouse1',
            tenant_id=uuid4(),
            client_id=uuid4(),
            region='us-east-1',
            kek_kid=uuid4()
        )

        result = integration_profile_from_orm(integration_orm)

        self.assertIsInstance(result, IntegrationProfile)
        self.assertEqual(result.id, integration_id)
        self.assertEqual(result.auth, Auth.password_proxy)
        self.assertEqual(result.cloud, Cloud.snowflake_managed)
        self.assertEqual(result.db, DB.snowflake)
        self.assertEqual(result.connection_name, 'test_connection')
        self.assertEqual(result.database_name, 'test_db')
        self.assertEqual(result.host, 'test.example.com')
        self.assertEqual(result.port, 443)
        self.assertTrue(result.autosync_on)

    def test_only_includes_profile_fields(self):
        integration_orm = IntegrationORM(
            id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            auth=Auth.cert,
            cloud=Cloud.aws,
            db=DB.postgresql,
            connection_name='profile_test',
            database_name='db',
            host='localhost',
            port=3306,
            autosync_on=False,
            kek_kid=uuid4(),
            warehouse='secret_warehouse',
            tenant_id=uuid4()
        )

        result = integration_profile_from_orm(integration_orm)

        self.assertFalse(hasattr(result, 'kek_kid'))
        self.assertFalse(hasattr(result, 'warehouse'))
        self.assertFalse(hasattr(result, 'organization_id'))
        self.assertFalse(hasattr(result, 'user_id'))


class TestIntegrationFromORM(unittest.TestCase):

    def setUp(self):
        self.integration_id = uuid4()
        self.organization_id = uuid4()
        self.user_id = uuid4()
        self.tenant_id = 'tenant_id'
        self.client_id = 'client_id'
        self.kek_kid = 'kek_kid'

    def test_converts_all_orm_fields(self):
        integration_orm = IntegrationORM(
            id=self.integration_id,
            organization_id=self.organization_id,
            user_id=self.user_id,
            auth=Auth.password_native,
            cloud=Cloud.aws,
            db=DB.mysql,
            connection_name='full_integration',
            host='prod.example.com',
            database_name='prod_db',
            kek_kid=self.kek_kid,
            port=443,
            warehouse='prod_warehouse',
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            region='us-west-2',
            azure_cert_kid='cert_456',
            azure_cert_name='azure_cert',
            azure_public_key_pem='-----BEGIN PUBLIC KEY-----\nAZURE_KEY',
            snowflake_public_key_pem='-----BEGIN PUBLIC KEY-----\nSNOWFLAKE_KEY',
            autosync_on=True
        )

        result = integration_from_orm(integration_orm)

        self.assertIsInstance(result, Integration)
        self.assertEqual(result.id, self.integration_id)
        self.assertEqual(result.organization_id, self.organization_id)
        self.assertEqual(result.user_id, self.user_id)
        self.assertEqual(result.auth, Auth.password_native)
        self.assertEqual(result.cloud, Cloud.aws)
        self.assertEqual(result.db, DB.mysql)
        self.assertEqual(result.connection_name, 'full_integration')
        self.assertEqual(result.host, 'prod.example.com')
        self.assertEqual(result.database_name, 'prod_db')
        self.assertEqual(result.kek_kid, self.kek_kid)
        self.assertEqual(result.port, 443)
        self.assertEqual(result.warehouse, 'prod_warehouse')
        self.assertEqual(result.tenant_id, self.tenant_id)
        self.assertEqual(result.client_id, self.client_id)
        self.assertEqual(result.region, 'us-west-2')
        self.assertEqual(result.azure_cert_kid, 'cert_456')
        self.assertEqual(result.azure_cert_name, 'azure_cert')
        self.assertEqual(result.azure_public_key_pem, '-----BEGIN PUBLIC KEY-----\nAZURE_KEY')
        self.assertEqual(result.snowflake_public_key_pem, '-----BEGIN PUBLIC KEY-----\nSNOWFLAKE_KEY')
        self.assertTrue(result.autosync_on)

    def test_preserves_types(self):
        integration_orm = IntegrationORM(
            id=self.integration_id,
            organization_id=self.organization_id,
            user_id=self.user_id,
            auth=Auth.password_proxy,
            cloud=Cloud.gcp,
            db=DB.mysql,
            connection_name='test',
            host='localhost',
            database_name='test_db',
            kek_kid=self.kek_kid,
            port=5432,
            warehouse=None,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            region=None,
            azure_cert_kid=None,
            azure_cert_name=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=False
        )

        result = integration_from_orm(integration_orm)

        self.assertIsInstance(result.id, UUID)
        self.assertIsInstance(result.organization_id, UUID)
        self.assertIsInstance(result.user_id, UUID)
        self.assertIsInstance(result.kek_kid, str)
        self.assertIsInstance(result.tenant_id, str)
        self.assertIsInstance(result.client_id, str)

    def test_handles_optional_fields(self):
        integration_orm = IntegrationORM(
            id=self.integration_id,
            organization_id=self.organization_id,
            user_id=self.user_id,
            auth=Auth.password_native,
            cloud=Cloud.snowflake_managed,
            db=DB.snowflake,
            connection_name='minimal',
            host='localhost',
            database_name='db',
            kek_kid=self.kek_kid,
            port=3306,
            warehouse=None,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            region=None,
            azure_cert_kid=None,
            azure_cert_name=None,
            azure_public_key_pem=None,
            snowflake_public_key_pem=None,
            autosync_on=False
        )

        result = integration_from_orm(integration_orm)

        self.assertIsNone(result.warehouse)
        self.assertIsNone(result.region)
        self.assertIsNone(result.azure_cert_kid)
        self.assertIsNone(result.azure_cert_name)
        self.assertIsNone(result.azure_public_key_pem)
        self.assertIsNone(result.snowflake_public_key_pem)
        self.assertFalse(result.autosync_on)


class TestConversionRoundTrip(unittest.TestCase):

    def test_dto_to_domain_to_orm_to_domain(self):
        organization_id = uuid4()
        user_id = uuid4()
        tenant_id = 'tenant_id'
        client_id = 'client_id'
        kek_kid = 'kek_kid'

        original_dto = IntegrationCreateRequest(
            auth=Auth.cert,
            cloud=Cloud.azure,
            db=DB.sqlserver,
            connection_name='roundtrip_test',
            descr='test-descr',
            host='test.example.com',
            database_name='test_db',
            kek_kid=kek_kid,
            port=443,
            warehouse='test_warehouse',
            tenant_id=tenant_id,
            client_id=client_id,
            region='us-east-1',
            azure_cert_kid='cert_789',
            azure_cert_name='test_cert',
            azure_public_key_pem='-----BEGIN PUBLIC KEY-----',
            snowflake_public_key_pem='-----BEGIN PUBLIC KEY-----',
            autosync_on=True
        )

        domain = integration_create_from_dto(original_dto)
        orm = orm_from_integration_create(organization_id, user_id, domain)
        result = integration_from_orm(orm)

        self.assertEqual(result.auth, original_dto.auth)
        self.assertEqual(result.cloud, original_dto.cloud)
        self.assertEqual(result.db, original_dto.db)
        self.assertEqual(result.connection_name, original_dto.connection_name)
        self.assertEqual(result.host, original_dto.host)
        self.assertEqual(result.database_name, original_dto.database_name)
        self.assertEqual(result.kek_kid, original_dto.kek_kid)
        self.assertEqual(result.port, original_dto.port)
        self.assertEqual(result.warehouse, original_dto.warehouse)
        self.assertEqual(result.tenant_id, original_dto.tenant_id)
        self.assertEqual(result.client_id, original_dto.client_id)
        self.assertEqual(result.region, original_dto.region)
        self.assertEqual(result.autosync_on, original_dto.autosync_on)
        self.assertEqual(result.organization_id, organization_id)
        self.assertEqual(result.user_id, user_id)
