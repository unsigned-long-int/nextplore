import os

from dotenv import load_dotenv
from typing import Optional, NamedTuple

load_dotenv()


class Credentials(NamedTuple):
    openai_api_key: str
    sql_connection_string: str


def load_credentials() -> Optional[Credentials]:
    openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
    sql_connection_string: Optional[str] = os.getenv('SQL_CONNECTION_STRING')

    if openai_api_key is None:
        message = 'OPENAI_API_KEY is not found either in .env or environmental variable'
        raise SystemExit(message)

    if sql_connection_string is None:
        message = 'SQL_CONNECTION_STRING is not found either in .env or environmental variable'
        raise SystemExit(message)

    return Credentials(
        openai_api_key=openai_api_key,
        sql_connection_string=sql_connection_string
    )
