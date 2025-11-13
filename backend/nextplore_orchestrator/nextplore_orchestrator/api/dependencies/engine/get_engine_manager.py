from fastapi import Request

from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager


def get_engine_manager(request: Request) -> EngineManager:
    return request.app.state.engine_manager
