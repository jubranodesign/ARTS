import radon
from radon.raw import analyze
from radon.visitors import ComplexityVisitor
from radon.metrics import h_visit
import os
import pandas as pd


def extract_code_metrics(code_string):
    """
    מחלץ את המדדים המדויקים התואמים לאקסל של NASA:
    ['loc', 'v(g)', 'v', 'd', 'e', 'b']
    """
    try:
        # 1. חילוץ loc (נשתמש ב-lloc כי הוא הכי מדויק למדדי NASA)
        raw_metrics = analyze(code_string)
        loc = raw_metrics.lloc

        # 2. חילוץ v(g) - מורכבות ציקלומטית (ממוצע לקובץ)
        v = ComplexityVisitor.from_code(code_string)
        # אם יש פונקציות, ניקח ממוצע. אם הקובץ ריק, המורכבות היא 1.
        vg_list = [obj.complexity for obj in v.functions + v.classes]
        vg = sum(vg_list) / len(vg_list) if vg_list else 1

        # 3. חילוץ מדדי Halstead (v, d, e, b)
        halstead_metrics = h_visit(code_string)
        # אנחנו לוקחים את המדדים הכוללים (total) של הקובץ
        h_v = halstead_metrics.total.volume
        h_d = halstead_metrics.total.difficulty
        h_e = halstead_metrics.total.effort
        h_b = halstead_metrics.total.bugs

        return {
            'loc': loc,
            'v(g)': vg,
            'v': h_v,
            'd': h_d,
            'e': h_e,
            'b': h_b,
            'defects': None  # זה מה שהמודל יחזה בהמשך
        }
    except Exception as error:
        print(f"Error analyzing code: {error}")
        return None

# --- דוגמה לשימוש ---
# example_code = """
# def calculate_sum(a, b):
#     if a > b:
#         return a + b
#     else:
#         return b - a
# """

# metrics = extract_code_metrics(example_code)
# print(metrics)


def scan_repo_to_excel(repo_path, output_file='my_repo_metrics.csv'):
    all_metrics = []

    print(f"Starting scan for: {repo_path}")

    # מעבר על כל הקבצים בריפו
    for root, dirs, files in os.walk(repo_path):
        # סינון תיקיות לא רלוונטיות (כמו venv או .git)
        if any(ignored in root for ignored in ['venv', '.git', '__pycache__', 'node_modules']):
            continue

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    # חילוץ המדדים בעזרת הפונקציה שבנינו
                    metrics = extract_code_metrics(code)
                    
                    if metrics:
                        # הוספת שם הקובץ כדי שנדע מאיפה הנתונים הגיעו
                        metrics['file_name'] = file
                        metrics['file_path'] = os.path.relpath(file_path, repo_path)
                        all_metrics.append(metrics)
                        
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")

    # יצירת DataFrame ושמירה
    if all_metrics:
        df = pd.DataFrame(all_metrics)
        
        # סידור העמודות שיהיה נוח (השמות בדיוק כמו באקסל של נאס"א)
        column_order = ['file_name', 'loc', 'v(g)', 'v', 'd', 'e', 'b', 'file_path']
        df = df[column_order]
        
        # שמירה לאקסל (או ל-CSV אם אתה מעדיף)
        if output_file.endswith('.xlsx'):
            df.to_excel(output_file, index=False)
        else:
            df.to_csv(output_file, index=False)
            
        print(f"Success! Metrics saved to {output_file}")
        print(f"Total files scanned: {len(df)}")
        return df
    else:
        print("No Python files found or analyzed.")
        return None