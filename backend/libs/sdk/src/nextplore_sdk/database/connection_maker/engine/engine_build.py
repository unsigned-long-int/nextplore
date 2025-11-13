import asyncio
from typing import Any, Dict
from sqlalchemy.engine import Engine

from nextplore_sdk.database.connection_maker.exc.exceptions import MissingRegistry
from nextplore_sdk.database.connection_maker.models.connection_profile import ConnectionProfile
from nextplore_sdk.database.connection_maker.registry.auth_strategy_registry import STRATEGY_REGISTRY
from nextplore_sdk.database.connection_maker.engine.engine_invoke import invoke_engine


async def build_engine(profile: ConnectionProfile) -> Engine:
    key = (profile.cloud, profile.db, profile.auth)
    try:
        strategy_cls, adapter_cls, creds_provider_cls = STRATEGY_REGISTRY[key]
    except KeyError as e:
        raise MissingRegistry(f'Strategy is not found in registry for: {key}') from e

    strategy = strategy_cls(profile)
    adapter = adapter_cls()

    creator_kwargs: Dict[str, Any] = {'adapter': adapter}
    if creds_provider_cls:
        creator_kwargs['creds_provider'] = creds_provider_cls(profile)

    creator = strategy.make_creator(**creator_kwargs)
    return await asyncio.to_thread(
        invoke_engine,
        adapter_cls.DIALECT,
        creator=creator,
        **strategy.pool_settings()
    )
