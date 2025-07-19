from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError


from database.repositories import IntegrationRepository
from utils.encryption import encrypt_integration, DecryptedIntegration
from messaging.message_bus import get_kafka_message_bus
from messaging.events.integration_service import IntegrationCreated
from shared.contracts.integration_service import PreparedIntegrationCreateRequest



router = APIRouter(prefix='/v1/integration', tags=['Integration'])

@router.post('/create-integration', status_code=status.HTTP_204_NO_CONTENT)
def create_integration(payload: PreparedIntegrationCreateRequest) -> None:
    integration_repo = IntegrationRepository()

    decrypted_integration = DecryptedIntegration(
        **payload.model_dump()
    )
    try:
        encrypted_integration = encrypt_integration(decrypted_integration)
        integration_id = integration_repo.create_integration(encrypted_integration)
        get_kafka_message_bus().publish(IntegrationCreated(integration_id=integration_id))
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Database error: {str(e)}'
        )
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unhandled error: {str(e)}'
        )
    