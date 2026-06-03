from dataclasses import dataclass, field
from typing import Annotated, List, Literal


EditTag = Literal["LEKSYKA", "NATURALNOŚĆ", "ZWIĘZŁOŚĆ", "SKŁADNIA"]


@dataclass(frozen=True, slots=True)
class FieldDescription:
    text: str


@dataclass(slots=True)
class TranslatorExample:
    en: Annotated[str, FieldDescription("Zdanie źródłowe.")]
    context: Annotated[str, FieldDescription("Scena i rejestr.")]
    good: Annotated[str, FieldDescription("Wzorcowe tłumaczenie.")]
    bad: Annotated[str, FieldDescription("Typowe potknięcie.")] = ""
    note: Annotated[str, FieldDescription("Krótka lekcja z błędu.")] = ""


@dataclass(slots=True)
class EditChange:
    tag: Annotated[EditTag, FieldDescription("Rodzaj poprawki.")]
    change: Annotated[str, FieldDescription("Co zmieniono.")]
    reason: Annotated[str, FieldDescription("Dlaczego warto.")]


@dataclass(slots=True)
class EditorExample:
    en: Annotated[str, FieldDescription("Źródło jako kotwica.")]
    context: Annotated[str, FieldDescription("Scena i rejestr.")]
    robocze: Annotated[str, FieldDescription("Draft tłumacza.")]
    po_redakcji_good: Annotated[str, FieldDescription("Dobra redakcja.")]
    po_redakcji_bad: Annotated[str, FieldDescription("Zła redakcja.")]
    zmiany: Annotated[List[EditChange], FieldDescription("Lista poprawek.")] = field(default_factory=list)


@dataclass(slots=True)
class RaceStyle:
    race_name: Annotated[str, FieldDescription("Nazwa rasy.")]
    label: Annotated[str, FieldDescription("Krótki uchwyt stylu.")]
    voice: Annotated[str, FieldDescription("Tożsamość głosu.")]
    syntax_rhythm: Annotated[str, FieldDescription("Rytm i składnia.")]
    lexicon: Annotated[str, FieldDescription("Preferowana leksyka.")]
    avoid: Annotated[str, FieldDescription("Czego unikać.")]
    essence: Annotated[str, FieldDescription("Jednozdaniowa esencja.")]
    translator_examples: Annotated[List[TranslatorExample], FieldDescription("Przykłady tłumaczeń.")] = field(default_factory=list)
    editor_examples: Annotated[List[EditorExample], FieldDescription("Przykłady redakcji.")] = field(default_factory=list)
