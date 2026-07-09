from moduly.AI_RAG import insert_into_qdrant_collection


# INDEKSUJĘ DO QDRANTA TYLKO NOWE/ZMIENIONE DOKUMENTY RAG
# RESET=True czyści całą kolekcję Qdranta, więc używać tylko ręcznie/awaryjnie.
if __name__ == "__main__":
    insert_into_qdrant_collection(reset=False)