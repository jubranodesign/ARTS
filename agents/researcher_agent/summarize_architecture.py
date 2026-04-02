from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from langgraph.graph.state import RunnableConfig

from agents.researcher_agent.models import ArchitectureSnapshot
from agents.researcher_agent.prompts import ARCHITECT_SUMMARY_PROMPT
from graph.state import AgentState
from shared.config import setup_node_llm
from utils.utils import extract_message_by_content, extract_python_path, filter_only_successful_tests, get_all_processed_tool_data, get_clean_text


def summarize_architecture(state: AgentState, config: RunnableConfig):
    """
    צומת המסכם: לוקח את המחקר, מזקק אותו ל-ArchitectureSnapshot מפורק,
    בונה ממנו סיכום טקסטואלי ומנקה היסטוריה.
    """
    llm = setup_node_llm(config)
    structured_llm = llm.with_structured_output(ArchitectureSnapshot)

    all_messages = state.get("messages", [])
    # print(f" summarize_architecture all_messages: {all_messages}")
    user_task = state.get("user_input", "No specific task defined.")
    target_file = extract_python_path(user_task)
    
    test_chunks = get_all_processed_tool_data(all_messages, filter_func=filter_only_successful_tests)
    # print(f" summarize_architecture only_tests_data: {test_chunks}")

    raw_research = extract_message_by_content(all_messages, "### RESEARCH_DATA_DUMP ###")
    # print(f" summarize_architecture raw_research: {raw_research}")

    if not raw_research:
        print("❌ Critical Error: No '### RESEARCH_DATA_DUMP ###' found in Researcher history.")
        return {} # כאן ה-Flow ייעצר כי אין נתונים לסיכום
   
    # 2. ניקוי הטקסט (הסרת תגיות JSON או Markdown מיותרות שנצמדו ל-Dump)
    clean_research = get_clean_text(raw_research)
    # print(f" summarize_architecture clean_research: {clean_research}")

    combined_research = f"--- SOURCE CODE ---\n{clean_research}\n\n--- REFERENCE TEST CHUNKS ---\n{test_chunks}"
    print(f" summarize_architecture combined_research: {combined_research}")

    
    summary_instr = ARCHITECT_SUMMARY_PROMPT.format(
        research_data=combined_research,
        user_task=user_task,
    )

    input_messages = [
        SystemMessage(content=summary_instr),
        HumanMessage(content="Extract the technical facts into the structured schema now. Raw data only."),
    ]

    try:
        result = structured_llm.invoke(input_messages)

        if not result:
            raise ValueError("Structured output returned None")

        final_summary_text = result.to_summary_text()
        print(f"✅ Architecture snapshot updated. final_summary_text: {final_summary_text}")
        print(f"✅ Architecture snapshot updated. Confidence: {result.confidence_score}")

        delete_messages = [RemoveMessage(id=m.id) for m in all_messages if m.id]

        return {
            "architecture_summary": final_summary_text,
            "target_file": target_file,
            "messages": delete_messages
        }

    except Exception as e:
        print(f"❌ Error during structured invoke: {e}")
        return {}
