from typing import Literal
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage
from typing_extensions import Annotated, TypedDict


class QuestSummaryPL(TypedDict):
    """Podsumowanie misji."""

    Tytuł: Annotated[str, ..., "Tytuł misji"]


class QuestObjectivesPL(TypedDict):
    """Cele misji."""

    Główny: Annotated[dict[str, str], ..., "Główne cele misji mapowane numerem linii"]
    Podrzędny: Annotated[dict[str, str], ..., "Podrzędne cele misji mapowane numerem linii"]


class DialogueBlockPL(TypedDict):
    """Blok dialogowy misji."""

    id: Annotated[int, ..., "Identyfikator bloku dialogowego"]
    typ: Annotated[Literal["gossip", "dymek"], ..., "Typ bloku dialogowego"]
    npc_pl: Annotated[str, ..., "Polska nazwa NPC wypowiadającego kwestie w tym bloku"]
    wypowiedzi_PL: Annotated[dict[str, str], ..., "Kwestie dialogowe mapowane numerem linii"]


class QuestPL(TypedDict):
    """Polska treść misji."""

    Podsumowanie_PL: Annotated[QuestSummaryPL, ..., "Podsumowanie misji"]
    Cele_PL: Annotated[QuestObjectivesPL, ..., "Cele misji"]
    Treść_PL: Annotated[dict[str, str], ..., "Główna treść misji mapowana numerem linii"]
    Postęp_PL: Annotated[dict[str, str], ..., "Teksty postępu misji mapowane numerem linii"]
    Zakończenie_PL: Annotated[dict[str, str], ..., "Teksty zakończenia misji mapowane numerem linii"]
    Nagrody_PL: Annotated[dict[str, str], ..., "Sekcja nagród mapowana numerem linii"]


class DialoguesPL(TypedDict):
    """Polskie dialogi misji."""

    Gossipy_Dymki_PL: Annotated[list[DialogueBlockPL], ..., "Lista bloków dialogowych"]


class QuestContentResponse(TypedDict):
    """Pełna polska treść misji i dialogów."""

    Misje_PL: Annotated[QuestPL, ..., "Polska treść misji"]
    Dialogi_PL: Annotated[DialoguesPL, ..., "Polskie dialogi misji"]


class QuestContentResult(TypedDict):
    raw: AIMessage
    parsed: QuestContentResponse | None
    parsing_error: BaseException | None


QUEST_CONTENT_JSON_SCHEMA = {
    "title": "QuestContentResponse",
    "description": "Pełna polska treść misji i dialogów.",
    "type": "object",
    "properties": {
        "Misje_PL": {
            "type": "object",
            "properties": {
                "Podsumowanie_PL": {
                    "type": "object",
                    "properties": {
                        "Tytuł": {"type": "string"},
                    },
                    "required": ["Tytuł"],
                    "additionalProperties": False,
                },
                "Cele_PL": {
                    "type": "object",
                    "properties": {
                        "Główny": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                        "Podrzędny": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                    },
                    "required": ["Główny", "Podrzędny"],
                    "additionalProperties": False,
                },
                "Treść_PL": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "Postęp_PL": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "Zakończenie_PL": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "Nagrody_PL": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": [
                "Podsumowanie_PL",
                "Cele_PL",
                "Treść_PL",
                "Postęp_PL",
                "Zakończenie_PL",
                "Nagrody_PL",
            ],
            "additionalProperties": False,
        },
        "Dialogi_PL": {
            "type": "object",
            "properties": {
                "Gossipy_Dymki_PL": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "typ": {
                                "type": "string",
                                "enum": ["gossip", "dymek"],
                            },
                            "npc_pl": {"type": "string"},
                            "wypowiedzi_PL": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                        },
                        "required": ["id", "typ", "npc_pl", "wypowiedzi_PL"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["Gossipy_Dymki_PL"],
            "additionalProperties": False,
        },
    },
    "required": ["Misje_PL", "Dialogi_PL"],
    "additionalProperties": False,
}


class LoreQuestion(BaseModel):
    aspect: str = Field(description="The entity or theme this question targets, e.g. 'Lightbloom', 'Orweyna'")
    question: str = Field(description="A single English question about that aspect")


class QuestLoreResult(BaseModel):
    questions: list[LoreQuestion] = Field(min_length=2, max_length=3)
