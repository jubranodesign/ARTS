from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from langgraph.graph.state import RunnableConfig
from agents.researcher_agent.prompts import ARCHITECT_SUMMARY_PROMPT
from graph.state import AgentState
from shared.config import setup_node_llm
from utils.utils import extract_message_by_content, filter_only_successful_tests, get_all_processed_tool_data, get_clean_text
import re
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage

def summarize_architecture(state: AgentState, config: RunnableConfig):
    """
    צומת המסכם: שומר על ה-RESEARCH_DATA_DUMP המקורי מהחוקר, ומחלץ
    דוגמת זהב (Golden Example) של טסטים באמצעות LLM רק אם קיימים כאלו.
    """
    llm = setup_node_llm(config)

    all_messages = state.get("messages", [])
    user_task = state.get("user_input", "No specific task defined.")
    
    # 1. שליפת חתיכות הטסטים וה-Dump מהחוקר
    raw_test_chunks = get_all_processed_tool_data(all_messages, filter_func=filter_only_successful_tests)
    raw_research = extract_message_by_content(all_messages, "### RESEARCH_DATA_DUMP ###")
    print(f" raw_test_chunks: {raw_test_chunks}")
        
    if not raw_research:
        print("❌ Critical Error: No '### RESEARCH_DATA_DUMP ###' found in Researcher history.")
        return {}
    
    clean_research = get_clean_text(raw_research)
    print(f" summarize_architecture clean_research: {clean_research}")

    # ערכי ברירת מחדל למקרה שאין טסטים במאגר
    golden_test_summary = "None"
    confidence_score = 0.0

    # 🎯 קריאה ל-LLM תתבצע אך ורק אם קיימים טסטים מוצלחים במאגר
    if raw_test_chunks.strip():
        test_chunks_formatted = f"--- REFERENCE TEST CHUNKS ---\n{raw_test_chunks}"
        print(f" test_chunks: {test_chunks_formatted}")
        
        summary_instr = ARCHITECT_SUMMARY_PROMPT.format(
            test_chunks=test_chunks_formatted,
            user_task=user_task,
        )

        input_messages = [
            SystemMessage(content=summary_instr),
            HumanMessage(content="Extract the golden test pattern now as raw text."),
        ]

        try:
            response = llm.invoke(input_messages)
            raw_content = response.content.strip() if response else "None"

            score_match = re.search(r"CONFIDENCE_SCORE:\s*([\d\.]+)", raw_content)
            if score_match:
                confidence_score = float(score_match.group(1))
                golden_test_summary = re.sub(r"CONFIDENCE_SCORE:\s*[\d\.]+", "", raw_content).strip()
            else:
                golden_test_summary = raw_content

            if not golden_test_summary or golden_test_summary.lower() == "none":
                golden_test_summary = "None"
                confidence_score = 0.0

        except Exception as e:
            print(f"❌ Error during LLM invoke: {e}")
            raise e
    else:
        print("No successful reference tests discovered in vector store. Skipping LLM call.")

    # 🎯 מקום אחד מרכזי ואחיד להדפסת הלוגים של העדכון
    print(f"✅ Architecture snapshot updated. Golden Tests Summary Extracted!: {golden_test_summary}")
    print(f"✅ Architecture snapshot updated. Confidence: {confidence_score}")

    # ניקוי הודעות והחזרת המבנה ל-State
    delete_messages = [RemoveMessage(id=m.id) for m in all_messages if m.id]
    
    return {
        "architecture_summary": clean_research,
        "golden_test_summary": golden_test_summary,
        "messages": delete_messages,
        "target_file_code": ""
    }