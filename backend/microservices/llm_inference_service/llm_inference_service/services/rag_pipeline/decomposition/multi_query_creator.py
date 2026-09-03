EXPANSION_PROMPT = """Generate {multiplier} different search queries for the following question.
Each query should approach the topic from a different angle.
Return ONLY the queries, one per line, no numbering or explanation.

Original query: {query}"""


def expand_query(query: str, multiplier: int = 3) -> str:
    return EXPANSION_PROMPT.format(multiplier=multiplier, query=query)
