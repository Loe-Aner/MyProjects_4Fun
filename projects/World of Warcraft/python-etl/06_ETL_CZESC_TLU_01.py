from moduly.ai_batch_tlumacz_anthropic import main

# ==== PRZYKŁADY WYWOŁANIA ====
# .\.venv\Scripts\python.exe python-etl\06_ETL_CZESC_TLU_01_SONNET_BATCH.py submit --ids 12345
# .\.venv\Scripts\python.exe python-etl\06_ETL_CZESC_TLU_01_SONNET_BATCH.py submit --dodatek "Midnight" --limit 75
# .\.venv\Scripts\python.exe python-etl\06_ETL_CZESC_TLU_01_SONNET_BATCH.py retrieve
# .\.venv\Scripts\python.exe python-etl\06_ETL_CZESC_TLU_01_SONNET_BATCH.py retrieve --job-name msgbatch_... --validate-only
# .\.venv\Scripts\python.exe python-etl\06_ETL_CZESC_TLU_01_SONNET_BATCH.py submit --ids 12345 --retry-failed

if __name__ == "__main__":
    main()
