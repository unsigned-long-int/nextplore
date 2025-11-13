python -m build -w -o backend/libs/.wheelhouse backend/libs/sdk
python -m build -w -o backend/libs/.wheelhouse backend/libs/messaging

PYTHONPATH="/Users/nik/personal_projects/nextplore/backend/libs/sdk/src" python3 -m unittest discover "microservices/ai_orm_context_service"
PYTHONPATH="/Users/nik/personal_projects/nextplore/backend/libs/sdk/src:/Users/nik/personal_projects/nextplore/backend/libs/messaging/src" python3 -m unittest discover "microservices/embedding_service"


PYTHONPATH="/Users/nik/personal_projects/nextplore/backend/libs/messaging/src" python3 -m unittest discover "libs/messaging"
PYTHONPATH="/Users/nik/personal_projects/nextplore/backend/libs/sdk/src" python3 -m unittest discover "libs/sdk"
