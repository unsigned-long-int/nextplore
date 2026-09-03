
from pydantic import UUID4, BaseModel


class FilteredCrawlRequest(BaseModel):
    integrations: list[UUID4]
    schemas: dict[UUID4, list[str]]
    tables: dict[UUID4, list[str]]
