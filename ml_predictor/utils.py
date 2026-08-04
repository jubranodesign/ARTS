import logging
import os
import pickle

import numpy as np
import pandas as pd
from radon.complexity import cc_visit
from radon.metrics import h_visit
from radon.raw import analyze
from tabulate import tabulate

logger = logging.getLogger(__name__)

# Columns expected by bug_prediction_model.pkl / scaler.pkl (train.py / Radon path)
RISK_FEATURE_COLUMNS = [
    "loc",
    "v(g)",
    "v",
    "d",
    "e",
    "complexity_density",
    "volume_per_line",
]

# משתנים גלובליים לטעינה חד-פעמית
_model = None
_scaler = None

def load_ml_assets():
    global _model, _scaler
    if _model is None or _scaler is None:
        # מקבלים את תיקיית השורש של הפרויקט (איפה שיושב הקובץ הנוכחי)
        base_dir = os.path.dirname(__file__)
        
        # בונים נתיב מדויק לתיקיית המודלים
        model_path = os.path.join(base_dir, 'models', 'random_forest', 'bug_prediction_model.pkl')
        scaler_path = os.path.join(base_dir, 'models', 'random_forest', 'scaler.pkl')
        
        # בדיקת בטיחות (Senior Move): וודא שהקובץ קיים לפני הפתיחה
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        with open(model_path, 'rb') as f:
            _model = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            _scaler = pickle.load(f)
            
    return _model, _scaler


def _normalize_metrics_dataframe(df: pd.DataFrame) -> pd.DataFrame | None:
    if df is None or df.empty:
        return None
    missing = [c for c in RISK_FEATURE_COLUMNS if c not in df.columns]
    if missing:
        logger.error("Metrics extractor missing columns: %s", missing)
        return None
    out = df[RISK_FEATURE_COLUMNS].copy()
    out.replace([np.inf, -np.inf], np.nan, inplace=True)
    out.fillna(0, inplace=True)
    return out


def extract_code_metrics_radon(code_string: str) -> pd.DataFrame | None:
    """Radon-based JM1-aligned features (Python source only)."""
    try:
        raw_metrics = analyze(code_string)
        loc = raw_metrics.lloc

        v_visitor = cc_visit(code_string)
        vg_list = [obj.complexity for obj in v_visitor]
        vg = sum(vg_list) / len(vg_list) if vg_list else 1

        halstead = h_visit(code_string)
        v = halstead.total.volume
        d = halstead.total.difficulty
        e = halstead.total.effort

        complexity_density = vg / max(loc, 1)
        volume_per_line = v / max(loc, 1)

        data = [[loc, vg, v, d, e, complexity_density, volume_per_line]]
        df = pd.DataFrame(data, columns=RISK_FEATURE_COLUMNS)

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.fillna(0, inplace=True)

        if not df.empty:
            table_output = tabulate(df, headers="keys", tablefmt="psql", showindex=False)
            logger.debug("Feature breakdown (Radon):\n%s", table_output)

        return df

    except Exception as error:
        logger.error("Radon metric extraction failed: %s", error)
        return None


def extract_code_metrics(code_string: str, repo_path: str | None = None) -> pd.DataFrame | None:
    """
    JM1-aligned feature vector for predict_risk.
    BYOR extractor (env or .arts/metrics.py), else Radon when REPO_LANGUAGE is python.
    """
    from shared.repo_language import is_python_pipeline
    from utils.metrics_loader import resolve_metrics_extractor

    extractor = resolve_metrics_extractor(repo_path)
    if extractor is not None:
        try:
            raw = extractor(code_string)
            if isinstance(raw, pd.DataFrame):
                return _normalize_metrics_dataframe(raw)
            if isinstance(raw, dict):
                row = {k: raw.get(k, 0) for k in RISK_FEATURE_COLUMNS}
                return _normalize_metrics_dataframe(pd.DataFrame([row]))
            logger.error("Metrics extractor returned unsupported type: %s", type(raw))
            return None
        except Exception as error:
            logger.error("BYOR metrics extractor failed: %s", error)
            return None

    if is_python_pipeline():
        return extract_code_metrics_radon(code_string)

    logger.warning(
        "No metrics extractor for non-Python REPO_LANGUAGE. "
        "Set ARTS_METRICS_EXTRACTOR or add REPO_PATH/.arts/metrics.py"
    )
    return None


def predict_risk(file_content, repo_path: str | None = None):
    model, scaler = load_ml_assets()
    features_df = extract_code_metrics(file_content, repo_path=repo_path)
    if features_df is None:
        return 1.0, [
            (
                "metrics_extractor",
                {
                    "importance": 1.0,
                    "value": 0.0,
                },
            )
        ]

    scaled_features = scaler.transform(features_df)

    probability = model.predict_proba(scaled_features)[:, 1][0]

    # חילוץ חשיבות המשתנים הגלובלית מהמודל
    importances = model.feature_importances_
    feature_names = features_df.columns
    
    # יצירת מילון של המשתנים והערכים שלהם לקובץ הספציפי הזה
    # זה יעזור לסוכן להגיד: "זיהיתי סיכון בגלל שערך ה-LOC הוא X"
    explanation = {
        name: {"importance": float(imp), "value": float(val)}
        for name, imp, val in zip(feature_names, importances, features_df.values[0])
    }
    
    # מיון לפי החשיבות הכי גבוהה (ה-Top 3 שגרמו להחלטה)
    top_reasons = sorted(explanation.items(), key=lambda x: x[1]['importance'], reverse=True)[:3]

    return float(probability), top_reasons


def scan_repo_to_excel(repo_path, output_file='my_repo_metrics.csv'):
    all_metrics = []

    logger.info("Starting scan for: %s", repo_path)

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
                    logger.warning("Could not read file %s: %s", file_path, e)

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
            
        logger.info("Metrics saved to %s (total files scanned: %s)", output_file, len(df))
        return df
    else:
        logger.warning("No Python files found or analyzed.")
        return None
