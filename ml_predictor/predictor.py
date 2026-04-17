import joblib
from .utils import extract_metrics_from_code # פונקציית ה-Extractor שלך

# טעינת המודל פעם אחת בזיכרון
model = joblib.load('ml_predictor/model/random_forest/bug_prediction_model.pkl')
scaler = joblib.load('ml_predictor/model/random_forest/scaler.pkl')


def predict_bug_probability(code_content):
    # 1. הפיכת הקוד למספרים בעזרת Radon (Extractor)
    features = extract_metrics_from_code(code_content)
    
    # 2. ביצוע החיזוי
    probability = model.predict_proba([features])[0][1]
    
    return probability