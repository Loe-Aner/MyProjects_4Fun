from dataclasses import dataclass, field
from typing import List, Literal


EditTag = Literal["LEKSYKA", "NATURALNOŚĆ", "ZWIĘZŁOŚĆ", "SKŁADNIA"]


@dataclass(slots=True)
class TranslatorExample:
    en: str           # zdanie źródłowe
    context: str      # scena/rejestr, np. "walka", "neutralny z nutą humoru"
    good: str         # dobre tłumaczenie EN -> PL
    bad: str = ""     # wiarygodne potknięcie
    note: str = ""    # czego uczy wersja bad, np. "zbyt literacko"


@dataclass(slots=True)
class EditChange:
    tag: EditTag      # LEKSYKA / NATURALNOŚĆ / ZWIĘZŁOŚĆ / SKŁADNIA
    change: str       # np. "stworzeniami -> bytami"
    reason: str       # dlaczego ta zmiana


@dataclass(slots=True)
class EditorExample:
    en: str                # źródło — kotwica wierności, nie główny sygnał
    context: str
    robocze: str           # wejście redaktora (draft tłumacza)
    po_redakcji_good: str  # wyjście redaktora (wzorcowa wersja)
    po_redakcji_bad: str   # wyjście redaktora (zła wersja)
    zmiany: List[EditChange] = field(default_factory=list)


@dataclass(slots=True)
class RaceStyle:
    race_name: str
    label: str            # krótki uchwyt, np. "organiczna prostolinijność"
    voice: str            # kto mówi i jak: rejestr + tożsamość głosu
    syntax_rhythm: str    # długość i budowa zdań, ew. zmiana w walce
    lexicon: str          # tendencja leksykalna
    avoid: str            # czego nie robić: rejestry, słowa, maniery
    essence: str          # jednozdaniowy hak oddający duszę rasy
    translator_examples: List[TranslatorExample] = field(default_factory=list)
    editor_examples: List[EditorExample] = field(default_factory=list)