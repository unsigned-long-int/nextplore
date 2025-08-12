from openai import AsyncOpenAI


def load_open_ai_client(api_key: str) -> AsyncOpenAI:
    client = AsyncOpenAI(api_key=api_key)
    return client
