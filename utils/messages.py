from langchain_core.messages import SystemMessage, trim_messages
from langchain_core.messages import HumanMessage, ToolMessage


def get_clean_text(content):
    """
    Extracts plain text from LangChain message content.
    Handles both simple strings and Gemini's complex block format.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            block["text"] for block in content
            if isinstance(block, dict) and "text" in block
        )
    return str(content)


def get_trimmed_messages(messages, llm, max_tokens=3000):
    """
    מקבלת רשימת הודעות ומחזירה אותן גזורות לפי המכסה המבוקשת.
    תמיד שומרת על הודעת ה-System.
    """
    trimmer = trim_messages(
        max_tokens=max_tokens,
        strategy="last",
        token_counter=llm,
        # include_system=True,
        allow_partial=False
    )
    return trimmer.invoke(messages)


def build_agent_messages(state, system_msg, target_file, execute_instruction, llm):
    """
    בונה הודעות בצורה חכמה:
    שלב 1: [System, Human(Read)]
    שלב 2: [Trimmed History (שכבר מכילה את ה-System מראשיתה), Human(Execute)]
    """
    messages = state.get("messages", [])

    already_done_read = any(
        isinstance(m, ToolMessage) and m.name == "read_local_file"
        for m in messages
    )

    if not already_done_read:
        return [
            system_msg,
            HumanMessage(content=f"Please read the file: {target_file}")
        ]

    # ניקוי המערכת הישנה מההיסטוריה
    clean_history = [m for m in messages if not isinstance(m, SystemMessage)]
    
    trimmed_history = get_trimmed_messages(
        clean_history,
        llm,
        max_tokens=4000
    )
    return [system_msg] + trimmed_history + [HumanMessage(content=execute_instruction)]
