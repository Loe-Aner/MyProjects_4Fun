from moduly.ai_batch_redaktor_gemini import main

# ==== PRZYKLADY WYWOLANIA ====
# .\.venv\Scripts\python.exe python-etl\05_ETL_CZESC_TLU_02.py submit --fabula "The Light's Summons"
# .\.venv\Scripts\python.exe python-etl\05_ETL_CZESC_TLU_02.py submit --dodatek "Midnight"
# .\.venv\Scripts\python.exe python-etl\05_ETL_CZESC_TLU_02.py submit --dodatek "Midnight" --limit 75
# .\.venv\Scripts\python.exe python-etl\05_ETL_CZESC_TLU_02.py submit --kraina "The Jade Forest" --fabula "nazwa linii"

if __name__ == "__main__":
    main()
