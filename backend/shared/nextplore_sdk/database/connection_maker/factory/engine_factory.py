from sqlalchemy import Engine, create_engine

from connection_maker.exceptions.exceptions import MissingRegistry
from connection_maker.registry.auth_strategy_registry import STRATEGY_REGISTRY
from connection_maker.models.connection_profile import ConnectionProfile


def build_engine(profile: ConnectionProfile, **strategy_kwargs) -> Engine:
    key = (profile.cloud, profile.db, profile.auth)
    try:
        strategy_cls, adapter_cls, creds_provider_cls = STRATEGY_REGISTRY.get[key]
    except KeyError as e:
        raise MissingRegistry(f'Strategy is not found in registry for: {key}') from e
    
    strategy = strategy_cls(profile=profile, **strategy_kwargs)
    adapter = adapter_cls()
    if not creds_provider_cls:
        creator = strategy.make_creator(adapter)
        return create_engine(
            adapter_cls.DIALECT,
            creator=creator,
            **strategy.pool_settings()
        )

    creds_provider = creds_provider_cls(profile)
    creator = strategy.make_creator(adapter, creds_provider=creds_provider)
    return create_engine(
        adapter_cls.DIALECT,
        creator=creator,
        **strategy.pool_settings()
    )
    
