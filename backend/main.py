from typing import Dict, Any
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from infrastructure.authentication import verify_token

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
@app.get('/me')
async def get_me(user=Depends(verify_token)) -> Dict[str, Any]:
    return {'email': user['preferred_username'], 'name': user.get('name')}

app.include_router(api_router, prefix='/api')

