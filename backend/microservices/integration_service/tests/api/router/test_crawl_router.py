import unittest
from uuid import uuid4
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from pydantic import SecretStr

from integration_service.domain.exceptions import MissingAuth
from integration_service.domain.mappers.integration import to_dto_auth, to_dto_cloud, to_dto_db
from integration_service.domain.models.integration import Integration, Auth, DB, Cloud
from integration_service.cache import get_cache_service
from integration_service.api.router.connection_profile_router import router
from integration_service.api.dependencies import get_backend_connector
from integration_service.api.models.integration_connection_profile import (
    IntegrationConnectionProfile,
)
from integration_service.database.exceptions import IntegrationGetFailed, SecretsGetFailed

