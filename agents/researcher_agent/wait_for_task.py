from graph.state import AgentState
from ml_predictor.utils import predict_risk
from shared.config import REPO_PATH
from utils.paths import extract_python_path, get_safe_full_path


# def wait_for_task(state: AgentState):
#     # כאן הגרף עוצר. כשתריץ אותו שוב עם קלט (user_input),
#     # הוא ימשיך מהמקום הזה.
#     return state


def wait_for_task(state: AgentState):
    print("wait_for_task")
    # נניח שתוכן הקובץ נמצא ב-state או שאנחנו קוראים אותו מנתיב
    user_task = state.get("user_input")
    target_file = extract_python_path(user_task)
    full_path = get_safe_full_path(REPO_PATH, target_file)

    with open(full_path, "r") as f:
        code_content = f.read()

    risk, top_reasons = predict_risk(code_content)
    
    # הכנת הרשימה ל-State
    reasons_for_state = []
    for feat, data in top_reasons:
        reasons_for_state.append({
            "feature": feat,
            "impact": float(data['importance']),
            "value": float(data['value'])
        })

    # הדפסה למשתמש (אופציונלי, כדי שיראה בזמן אמת)
    # print("\n[AI Risk Analysis] Top Factors:")
    # for r in reasons_for_state:
    #     print(f" - {r['feature']}: Impact {r['impact']:.2f}, Value: {r['value']}")

    # new_input = input("\nYour task? (Enter to use AI Risk Assessment): ")

    return {
        "risk_score": float(risk),
        "risk_reasons": reasons_for_state, # נשמר ב-State לסבבים הבאים
        # "user_input": new_input if new_input.strip() else state.get("user_input")
    }