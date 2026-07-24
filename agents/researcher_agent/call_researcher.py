from langchain_core.messages import SystemMessage
from langgraph.graph.state import RunnableConfig
from agents.researcher_agent.prompts import RESEARCHER_SYSTEM_PROMPT
from agents.researcher_agent.tools import RESEARCHER_TOOLS
from graph.state import AgentState
from shared.config import setup_node_llm
from utils.paths import extract_python_path
from utils.repo_files import read_repo_text_tool_response
from utils.state import format_risk_context
from utils.utils import get_trimmed_messages

# הצמדת הכלים למופע המשותף

def call_researcher(state: AgentState, config: RunnableConfig):

    llm = setup_node_llm(config, RESEARCHER_TOOLS)

    # 1. שליפת נתונים - אנחנו סומכים על ה-main שהזין HumanMessage
    current_summary = state.get("architecture_summary", "No summary available yet.")
    user_task = state.get("user_input", "No task defined.")
    target_file = extract_python_path(user_task)
    all_messages = state.get("messages", [])
    risk_context = format_risk_context(state)
    target_file_content = state.get("target_file_code", None)
    
    # אם הוא לא קיים (סיבוב ראשון בלבד!), נקרא אותו עכשיו
    if not target_file_content:
        if target_file:
            repo_path = config["configurable"]["repo_path"]
            target_file_content = read_repo_text_tool_response(repo_path, target_file)
        else:
            target_file_content = "No target file path detected."
            
    # print("risk_context ", risk_context)
    # 2. בניית ה-System Message המעודכן
    # ה-user_task נשאר כאן כי הוא קריטי להנחיית המודל בכל סיבוב
   # 2. בניית ה-System Message המעודכן (משולב)
    instruction_content = f"""
    {RESEARCHER_SYSTEM_PROMPT}

    {risk_context}

    ### TARGET FILE PATH:
    {target_file}

    ### TARGET FILE SOURCE CODE (READ FIRST):
    ```python
    {target_file_content}
    ```

    ### TARGET TASK:
    {user_task}

    ### CURRENT ARCHITECTURE KNOWLEDGE:
    {current_summary}

    ### EXECUTION GUIDANCE:
    1. TECHNICAL FLOW: Analyze the TARGET FILE SOURCE CODE provided above. Identify its imports and core dependencies. Then, use 'search_dependencies_bm25' to inspect those dependencies, and 'search_golden_tests_semantic' to find reference test patterns.
    2. RISK ANALYSIS FOCUS: Focus your search and analysis on the logic related to the identified risk factors above. Your final data dump must explain how the code implementation contributes to these statistical risks.
    """

    system_msg = SystemMessage(content=instruction_content)

    # 3. סינון היסטוריה - משאירים רק Human, AI ו-Tool
    # אנחנו מעיפים את ה-SystemMessage הקודם כדי שג'מיני לא יתבלבל מהסדר
    clean_history = [m for m in all_messages if not isinstance(m, SystemMessage)]
    
    # 4. גזירה (Trim) למניעת חריגת טוקנים
    trimmed_history = get_trimmed_messages(clean_history, llm, max_tokens=50000)

    # 5. בניית הרשימה הסופית: [System, Human (מה-main), AI, Tool...]
    messages_to_send = [system_msg] + trimmed_history

    # 6. קריאה למודל
    try:
        response = llm.invoke(messages_to_send)

        # if "### RESEARCH_DATA_DUMP ###" in response.content:
        #  # שליפת ה-Ground Truth (נניח מה-config או מה-state)
        #  ground_truth = config.get("configurable", {}).get("ground_truth", None)
    
        #  if ground_truth:
        #     # שליחת הנתונים לאבחון
        #     eval_results = evaluate_quality(
        #     question=user_task,
        #     final_dump=response.content,
        #     message_history=trimmed_history, # ההיסטוריה שהמודל ראה בפועל
        #     ground_truth=ground_truth
        #     )
        #     print(f"eval_results: {eval_results}")
         
        #     report = evaluate_with_custom_judge(
        #                 judgment_model=ResearcherJudgment,
        #                 rubric=RESEARCHER_RUBRIC,
        #                 question=user_task,
        #                 answer=response.content,
        #                 message_history=trimmed_history
        #             )
        #     print(f"evaluate_with_custom_judge: {report}")
        state_update = {"messages": [response]}
        if not state.get("target_file_code") and target_file_content:
              state_update["target_file_code"] = target_file_content
              state_update["target_file"] = target_file
        return state_update     
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        # הדפסת סדר ההודעות לדיבאג במקרה של שגיאת פורמט
        print("Sequence: " + " -> ".join([type(m).__name__ for m in messages_to_send]))
        raise e