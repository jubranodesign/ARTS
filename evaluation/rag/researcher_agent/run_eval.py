# import json
# from evaluation.rag.eval_utils import run_evaluation_suite
# from your_project.agents import researcher_agent # הסוכן שלך

# # 1. טעינת ה-Dataset
# with open("evaluation/rag/researcher_agent/dataset.json", "r") as f:
#     golden_set = json.load(f)

# # 2. הרצת הסוכן על השאלות כדי לאסוף תוצאות (לפני האבחון)
# results_to_evaluate = []
# for item in golden_set:
#     # כאן אתה מריץ את ה-Graph/Agent שלך
#     final_state = researcher_agent.invoke({"user_input": item["question"]})
    
#     results_to_evaluate.append({
#         "question": item["question"],
#         "final_dump": final_state["messages"][-1].content,
#         "message_history": final_state["messages"][:-1],
#         "ground_truth": item["ground_truth"]
#     })

# # 3. הפעלת ה-Suite הכללית שבנית
# report = run_evaluation_suite(results_to_evaluate)

# # 4. הדפסת הממוצעים
# print(report)