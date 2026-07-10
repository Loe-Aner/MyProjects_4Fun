from langchain_openai import ChatOpenAI
from langchain_qwq import ChatQwen

from dotenv import load_dotenv
import warnings

load_dotenv()


warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings:",
    category=UserWarning,
    module="pydantic.main",
)

TEMPERATURE_LORE = 0.0
TEMPERATURE_CONTEXT = 0.05
TEMPERATURE_SUMMARY_QUEST = 0.0
TEMPERATURE_JSON_CORRECTOR = 0.0
TEMPERATURE_CHUNKER = 0.0
TEMPERATURE_TRANSLATOR = 0.60
TEMPERATURE_EDITOR = 0.65
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def llm_lore():
    llm = ChatOpenAI(
        model="gpt-5.6-terra",
        temperature=TEMPERATURE_LORE,
        reasoning_effort="medium",
        use_responses_api=True,
        max_retries=2
    )
    return llm

def llm_quest_summary():
    llm = ChatOpenAI(
        model="gpt-5.6-luna",
        temperature=TEMPERATURE_SUMMARY_QUEST,
        reasoning_effort="medium",
        use_responses_api=True,
        max_retries=2
    )
    return llm

def llm_context():
    llm = ChatOpenAI(
        model="gpt-5.6-luna",
        temperature=TEMPERATURE_CONTEXT,
        reasoning_effort="high",
        use_responses_api=True,
        max_retries=2
    )
    return llm

def llm_json_corrector():
    return ChatOpenAI(
        model="gpt-5.4-nano",
        temperature=TEMPERATURE_JSON_CORRECTOR,
        reasoning_effort="high",
        use_responses_api=True,
        max_retries=2
    )

def llm_chunker():
    return ChatOpenAI(
        model="gpt-5.4-nano",
        temperature=TEMPERATURE_CHUNKER,
        reasoning_effort="high",
        use_responses_api=True,
        max_retries=2
    )

def llm_translator() -> ChatQwen:
    return ChatQwen(
        model="qwen3.7-plus",
        temperature=TEMPERATURE_TRANSLATOR,
        top_p=0.95,
        enable_thinking=True,
        extra_body={
            "top_k": 20,
            "min_p": 0
        },
        max_retries=2,
    )

# ================ zastapiony gemini 3.1 pro ================
# def llm_editor() -> ChatQwen:
#     return ChatQwen(
#         model="qwen3.7-max",
#         temperature=TEMPERATURE_EDITOR,
#         top_p=0.95,
#         enable_thinking=True,
#         extra_body={
#             "top_k": 20,
#             "min_p": 0
#         },
#         max_retries=2,
#     )
