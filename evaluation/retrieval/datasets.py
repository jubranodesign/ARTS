
# TEST_SET מותאם לקוד ה-Scraper האמיתי
test_set = [
    # בדיקת לוגיקת מסד הנתונים ב-scraper.py
    ("how is the database session managed and committed", "session.commit()"),
    
    # בדיקת הטיפול בשגיאות (כאן חסר ה-rollback שדיברנו עליו!)
    ("database exception handling and try except block", "except Exception as e"),
    
    # בדיקת הקריאה ל-API ב-scraper_api.py
    ("where is the clinical trials api url defined", "clinicaltrials.gov"),
    
    # בדיקת הפרמטרים של ה-API
    ("how are page size and format parameters passed to requests", "params ="),
    
    # בדיקת הזרקת התלויות (Imports)
    ("which repositories are used to save studies", "from common.repositories import save_study")
]
