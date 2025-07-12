from openai import OpenAI


def load_open_ai_client(api_key: str) -> OpenAI:
    client = OpenAI(api_key=api_key)
    return client
