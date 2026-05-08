sample = {
    "question": "Analyze the database commit logic in the scraper.",
    
    # מה שהחוקר שלף בפועל מה-Vector DB
    "contexts": [
        "with get_session() as session: for study in studies: save_study(session, study) session.commit()"
    ],
    
    # ה-DUMP הסופי שהחוקר הוציא (ה-Answer שלו)
    "answer": """
    ### RESEARCH_DATA_DUMP ###
    - FILE_PATH: scraper_service/scraper.py
    - RAW_CODE_INSIGHTS: Uses get_session context manager, commits once after study loop.
    - DETECTED_IMPORTS: common.db, common.repositories, scraper_api
    - OBSERVATIONS: No explicit rollback handled in the try-except.
    """,
    
    # מה שאתה מצפה ממנו (הציון המושלם)
    "ground_truth": "The scraper commits changes after iterating through all fetched studies within a get_session context manager."
}