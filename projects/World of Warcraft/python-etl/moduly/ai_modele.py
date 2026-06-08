from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import warnings

load_dotenv()


warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings:",
    category=UserWarning,
    module="pydantic.main",
)

TEMPERATURE_LORE = 0.0
TEMPERATURE_CONTEXT = 0.0
TEMPERATURE_SUMMARY_QUEST = 0.0
TEMPERATURE_TRANSLATOR = 0.60 # pod qwen 3.7-plus, tak zalecaja
TEMPERATURE_EDITOR = 0.15
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def llm_lore():
    llm = ChatOpenAI(
        model="gpt-5.4",
        temperature=TEMPERATURE_LORE,
        reasoning_effort="medium",
        use_responses_api=True,
        max_retries=2
    )
    return llm

def llm_quest_summary():
    llm = ChatOpenAI(
        model="gpt-5.4-mini",
        temperature=TEMPERATURE_SUMMARY_QUEST,
        reasoning_effort="medium",
        use_responses_api=True,
        max_retries=2
    )
    return llm

def llm_context():
    llm = ChatOpenAI(
        model="gpt-5.4-mini",
        temperature=TEMPERATURE_CONTEXT,
        reasoning_effort="medium",
        use_responses_api=True,
        max_retries=2
    )
    return llm

def llm_translator():
    llm = ChatOpenAI(
        # model="minimax/minimax-m3",
        # model="qwen/qwen3.7-max",
        # model="qwen/qwen3.7-plus",
        # model="deepseek/deepseek-v4-pro",
        # model="x-ai/grok-4.3",
        # model="xiaomi/mimo-v2.5",
        model="google/gemini-3.5-flash",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url=OPENROUTER_BASE_URL,
        temperature=TEMPERATURE_TRANSLATOR,
        max_retries=2,
        default_headers={
            "X-Title": "World of Warcraft PL Translation",
        },
    )
    return llm

def llm_editor():
    llm = ChatOpenAI(
        model="gpt-5.5", # ZMIENIC
        temperature=TEMPERATURE_EDITOR,
        reasoning_effort="none",
        use_responses_api=True,
        max_retries=2
    )
    return llm
