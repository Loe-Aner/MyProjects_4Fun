import os

os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

import asyncio

from moduly.AI_RAG import wygeneruj_chunki_dla_pustych

bledy = asyncio.run(wygeneruj_chunki_dla_pustych(max_concurrency=35))