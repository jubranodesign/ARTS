
import os
from ml_predictor.utils import scan_repo_to_excel
from shared.config import REPO_PATH


if __name__ == "__main__":
    # 1. הגדר את הנתיב לתיקיית הפרויקט שלך (הנקודה אומרת "התיקייה שבה נמצא הסקריפט")
    path_to_my_repo = REPO_PATH
    
    # 2. הגדר את שם הקובץ שייווצר
    output_excel_name = 'my_repo_metrics.csv'
    
    # 3. הפעלת הפונקציה
    print(f"--- מתחיל סריקה של התיקייה: {os.path.abspath(path_to_my_repo)} ---")
    df_results = scan_repo_to_excel(path_to_my_repo, output_excel_name)
    
    # 4. הצגת סיכום קצר בטרמינל
    if df_results is not None:
        print("\n--- סריקה הושלמה בהצלחה! ---")
        print(f"נוצר קובץ אקסל בשם: {output_excel_name}")
        print("\n5 השורות הראשונות מהסריקה:")
        print(df_results.head())
    else:
        print("\n--- הסריקה הסתיימה ללא תוצאות ---")