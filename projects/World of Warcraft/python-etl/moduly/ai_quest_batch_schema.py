import copy
import json
from typing import Any


MAX_ZLOZONOSC_SCHEMATU_DIALOGOW = 80
MAX_OPCJONALNYCH_POL_ANTHROPIC = 24
SCHEMA_MODE_STRICT = "strict"
SCHEMA_MODE_RELAXED = "relaxed"


def _numbered_string_object_schema(source_mapping: Any) -> dict[str, Any]:
    keys = list((source_mapping or {}).keys()) if isinstance(source_mapping, dict) else []
    return {
        "type": "object",
        "properties": {str(key): {"type": "string"} for key in keys},
        "required": [str(key) for key in keys],
        "propertyOrdering": [str(key) for key in keys],
    }


def _klucze_wypowiedzi_dialogow(source_dialogues: list[Any]) -> list[str]:
    return sorted(
        {
            str(key)
            for block in source_dialogues
            if isinstance(block, dict)
            for key in (block.get("wypowiedzi_EN") or {}).keys()
        },
        key=lambda value: (0, int(value)) if value.isdigit() else (1, value),
    )


def metryki_schematu_dialogow(
    source_json: str,
    *,
    provider: str = "gemini",
) -> dict[str, int | str]:
    source = json.loads(source_json)
    source_dialogues = source.get("Dialogi_EN", {}).get("Gossipy_Dymki_EN", []) or []
    all_dialogue_keys = _klucze_wypowiedzi_dialogow(source_dialogues)
    liczba_blokow = len(source_dialogues)
    liczba_kluczy = len(all_dialogue_keys)
    zlozonosc = liczba_blokow * liczba_kluczy
    za_duzo_opcjonalnych_pol = (
        provider == "anthropic"
        and liczba_kluczy > MAX_OPCJONALNYCH_POL_ANTHROPIC
    )
    schema_mode = (
        SCHEMA_MODE_RELAXED
        if zlozonosc > MAX_ZLOZONOSC_SCHEMATU_DIALOGOW or za_duzo_opcjonalnych_pol
        else SCHEMA_MODE_STRICT
    )
    return {
        "schema_mode": schema_mode,
        "liczba_blokow": liczba_blokow,
        "liczba_kluczy": liczba_kluczy,
        "zlozonosc": zlozonosc,
    }


def quest_response_schema_dla_wsad_json(source_json: str) -> dict[str, Any]:
    """Schemat Gemini z dokładnymi numerowanymi kluczami misji źródłowej."""
    source = json.loads(source_json)
    source_quest = source.get("Misje_EN", {})
    source_dialogues = source.get("Dialogi_EN", {}).get("Gossipy_Dymki_EN", []) or []

    dialogue_properties: dict[str, Any] = {
        "id": {"type": "integer"},
        "typ": {"type": "string", "enum": ["gossip", "dymek"]},
        "npc_pl": {"type": "string"},
        "wypowiedzi_PL": {"type": "object"},
    }
    all_dialogue_keys = _klucze_wypowiedzi_dialogow(source_dialogues)
    if all_dialogue_keys:
        dialogue_properties["wypowiedzi_PL"] = {
            "type": "object",
            "properties": {key: {"type": "string"} for key in all_dialogue_keys},
            "propertyOrdering": all_dialogue_keys,
        }

    return {
        "type": "object",
        "properties": {
            "Misje_PL": {
                "type": "object",
                "properties": {
                    "Podsumowanie_PL": {
                        "type": "object",
                        "properties": {"Tytuł": {"type": "string"}},
                        "required": ["Tytuł"],
                    },
                    "Cele_PL": {
                        "type": "object",
                        "properties": {
                            "Główny": _numbered_string_object_schema(
                                source_quest.get("Cele_EN", {}).get("Główny")
                            ),
                            "Podrzędny": _numbered_string_object_schema(
                                source_quest.get("Cele_EN", {}).get("Podrzędny")
                            ),
                        },
                        "required": ["Główny", "Podrzędny"],
                    },
                    "Treść_PL": _numbered_string_object_schema(source_quest.get("Treść_EN")),
                    "Postęp_PL": _numbered_string_object_schema(source_quest.get("Postęp_EN")),
                    "Zakończenie_PL": _numbered_string_object_schema(source_quest.get("Zakończenie_EN")),
                    "Nagrody_PL": _numbered_string_object_schema(source_quest.get("Nagrody_EN")),
                },
                "required": [
                    "Podsumowanie_PL",
                    "Cele_PL",
                    "Treść_PL",
                    "Postęp_PL",
                    "Zakończenie_PL",
                    "Nagrody_PL",
                ],
            },
            "Dialogi_PL": {
                "type": "object",
                "properties": {
                    "Gossipy_Dymki_PL": {
                        "type": "array",
                        "minItems": len(source_dialogues),
                        "maxItems": len(source_dialogues),
                        "items": {
                            "type": "object",
                            "properties": dialogue_properties,
                            "required": ["id", "typ", "npc_pl", "wypowiedzi_PL"],
                            "propertyOrdering": ["id", "typ", "npc_pl", "wypowiedzi_PL"],
                        },
                    },
                },
                "required": ["Gossipy_Dymki_PL"],
            },
        },
        "required": ["Misje_PL", "Dialogi_PL"],
    }


def _przeksztalc_schema_dla_anthropic(value: Any) -> Any:
    if isinstance(value, list):
        return [_przeksztalc_schema_dla_anthropic(item) for item in value]
    if not isinstance(value, dict):
        return value

    transformed = {
        key: _przeksztalc_schema_dla_anthropic(item)
        for key, item in value.items()
        if key not in {"propertyOrdering", "minItems", "maxItems"}
    }
    if transformed.get("type") == "object":
        transformed["additionalProperties"] = False
    return transformed


def quest_response_schema_dla_anthropic(source_json: str) -> dict[str, Any]:
    """Wariant zgodny z Anthropic structured outputs."""
    schema = copy.deepcopy(quest_response_schema_dla_wsad_json(source_json))
    return _przeksztalc_schema_dla_anthropic(schema)


def _reorder_mapping_by_source(output_mapping: Any, source_mapping: Any) -> Any:
    if not isinstance(output_mapping, dict) or not isinstance(source_mapping, dict):
        return output_mapping

    ordered = {
        str(key): output_mapping[str(key)]
        for key in source_mapping.keys()
        if str(key) in output_mapping
    }
    for key, value in output_mapping.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def uporzadkuj_quest_json_wg_zrodla(
    parsed: dict[str, Any],
    source_json: str,
) -> dict[str, Any]:
    source = json.loads(source_json)
    source_quest = source.get("Misje_EN", {})
    source_dialogues = source.get("Dialogi_EN", {}).get("Gossipy_Dymki_EN", []) or []

    misje = parsed.get("Misje_PL", {})
    cele = misje.get("Cele_PL", {}) if isinstance(misje, dict) else {}
    if isinstance(cele, dict):
        cele["Główny"] = _reorder_mapping_by_source(
            cele.get("Główny"),
            source_quest.get("Cele_EN", {}).get("Główny"),
        )
        cele["Podrzędny"] = _reorder_mapping_by_source(
            cele.get("Podrzędny"),
            source_quest.get("Cele_EN", {}).get("Podrzędny"),
        )

    if isinstance(misje, dict):
        section_pairs = [
            ("Treść_PL", "Treść_EN"),
            ("Postęp_PL", "Postęp_EN"),
            ("Zakończenie_PL", "Zakończenie_EN"),
            ("Nagrody_PL", "Nagrody_EN"),
        ]
        for output_key, source_key in section_pairs:
            misje[output_key] = _reorder_mapping_by_source(
                misje.get(output_key),
                source_quest.get(source_key),
            )

    output_dialogues = parsed.get("Dialogi_PL", {}).get("Gossipy_Dymki_PL", [])
    if isinstance(output_dialogues, list):
        for index, output_block in enumerate(output_dialogues):
            if not isinstance(output_block, dict) or index >= len(source_dialogues):
                continue
            output_block["wypowiedzi_PL"] = _reorder_mapping_by_source(
                output_block.get("wypowiedzi_PL"),
                (source_dialogues[index] or {}).get("wypowiedzi_EN"),
            )

    return parsed
