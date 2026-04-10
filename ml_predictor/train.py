import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_model():
    # 1. טעינת הנתונים (CSV)
    df = pd.read_csv('ml_predictor/data/training_data.csv')
    
    # 2. עיבוד נתונים (Preprocessing)
    X = df[['complexity', 'maintainability', 'loc']] # המטריקות של Radon
    y = df['has_bug'] # המטרה (Target)
    
    # 3. אימון המודל
    model = RandomForestClassifier()
    model.fit(X, y)
    
    # 4. שמירת המודל לשימוש עתידי
    joblib.dump(model, 'ml_predictor/models/bug_model.pkl')
    print("Model trained and saved successfully!")

if __name__ == "__main__":
    train_model()