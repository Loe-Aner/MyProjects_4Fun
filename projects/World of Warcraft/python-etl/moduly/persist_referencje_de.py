from sqlalchemy import text
from sqlalchemy.engine import Engine

STATUS_REFERENCJA = "4_REFERENCJA"

_MAPA_SEKCJI_DE = {
    "Treść_DE": "TREŚĆ",
    "Postęp_DE": "POSTĘP",
    "Zakończenie_DE": "ZAKOŃCZENIE",
}

_Q_INSERT = text("""
    INSERT INTO dbo.MISJE_STATUSY (MISJA_ID_MOJE_FK, SEGMENT, PODSEGMENT, STATUS, NR, TRESC)
    VALUES (:misja_id, :segment, :podsegment, :status, :nr, :tresc)
""")

_Q_DELETE = text("""
    DELETE FROM dbo.MISJE_STATUSY
    WHERE MISJA_ID_MOJE_FK = :misja_id
      AND STATUS = :status
""")


def zbuduj_wiersze_referencji(misja_id: int, dane: dict) -> list[dict]:
    """Zamienia słownik z parsera na listę wierszy gotowych do insertu."""
    wiersze = []

    cele = dane.get("Cele_DE") or {}

    for nr, tresc in (cele.get("Główny") or {}).items():
        wiersze.append({
            "misja_id": misja_id, "segment": "CEL", "podsegment": "GŁÓWNY_CEL",
            "status": STATUS_REFERENCJA, "nr": int(nr), "tresc": tresc,
        })

    for nr, tresc in (cele.get("Podrzędny") or {}).items():
        wiersze.append({
            "misja_id": misja_id, "segment": "CEL", "podsegment": "PODRZĘDNY_CEL",
            "status": STATUS_REFERENCJA, "nr": int(nr), "tresc": tresc,
        })

    for klucz, segment in _MAPA_SEKCJI_DE.items():
        for nr, tresc in (dane.get(klucz) or {}).items():
            wiersze.append({
                "misja_id": misja_id, "segment": segment, "podsegment": None,
                "status": STATUS_REFERENCJA, "nr": int(nr), "tresc": tresc,
            })

    return wiersze


def zapisz_referencje_de(silnik: Engine, misja_id: int, dane: dict, nadpisz: bool = True) -> int:
    """
    Wstawia treść DE do MISJE_STATUSY jako 4_REFERENCJA (wszystko w jednej transakcji).

    nadpisz=True -> najpierw kasuje istniejące wiersze 4_REFERENCJA tej misji,
    dzięki czemu ponowne uruchomienie nie tworzy duplikatów (na tym statusie
    nie ma unikalnego indeksu, który by je blokował).

    Zwraca liczbę wstawionych wierszy.
    """
    wiersze = zbuduj_wiersze_referencji(misja_id, dane)

    if not wiersze:
        print(f"[{misja_id}] Brak treści DE do zapisania — pomijam.")
        return 0

    with silnik.begin() as conn:
        if nadpisz:
            usuniete = conn.execute(_Q_DELETE, {"misja_id": misja_id, "status": STATUS_REFERENCJA}).rowcount
            if usuniete:
                print(f"[{misja_id}] Usunięto {usuniete} starych wierszy {STATUS_REFERENCJA}.")
        conn.execute(_Q_INSERT, wiersze)

    print(f"[{misja_id}] Zapisano {len(wiersze)} wierszy jako {STATUS_REFERENCJA}.")
    return len(wiersze)
