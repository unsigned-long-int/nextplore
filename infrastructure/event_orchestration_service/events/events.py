from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    message: str


@dataclass(frozen=True)
class OpenAICredentialsLoadFailed(Event):
    pass


@dataclass(frozen=True)
class SQLConnectionStringLoadFailed(Event):
    pass


@dataclass(frozen=True)
class OpenAIClientLoadFailed(Event):
    pass


@dataclass(frozen=True)
class ManifestNotFound(Event):
    pass


@dataclass(frozen=True)
class ManifestDecodingFailed(Event):
    pass


@dataclass(frozen=True)
class MissingManifestItemsEncountered(Event):
    pass


@dataclass(frozen=True)
class ManifestGenerationFailed(Event):
    pass


@dataclass(frozen=True)
class TableDescriptorGenerationFailed(Event):
    pass


@dataclass(frozen=True)
class SchemaDescriptorNotFound(Event):
    pass


@dataclass(frozen=True)
class TableDescriptorNotFound(Event):
    pass


@dataclass(frozen=True)
class ReflectedColumnNotFound(Event):
    pass
