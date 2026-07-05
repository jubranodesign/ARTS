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
        max_tokens=10000
    )
    return [system_msg] + trimmed_history + [HumanMessage(content=execute_instruction)]

# def build_agent_messages(state, system_msg, target_file, execute_instruction, llm):
#     messages = state.get("messages", [])

#     # 1. נחלץ את כל הודעות הכלי של קריאת קבצים שיש בהן תוכן
#     tool_messages = [
#         m for m in messages 
#         if isinstance(m, ToolMessage) and m.name == "read_local_file"
#     ]
    
#     # סינון נוסף לפי פונקציית הניקוי שלך
#     clean_tool_history = [m for m in tool_messages if get_clean_text(m.content)]

#     # 2. אם אין הודעות כלי תקינות, סימן שעדיין צריך לקרוא את הקובץ
#     if not clean_tool_history:
#         return [
#             system_msg,
#             HumanMessage(content=f"Please read the file: {target_file}")
#         ]

#     # 3. שלב הביצוע - לוקחים רק את ה-ToolMessages הנקיים
#     # הערה: אם אתה רוצה רק את הקובץ האחרון שנקרא, אפשר להשתמש ב- [clean_tool_history[-1]]
#     trimmed_history = get_trimmed_messages(
#         clean_tool_history,
#         llm,
#         max_tokens=4000
#     )
    
#     # מחזירים מבנה נקי: מערכת -> תוכן הקבצים -> הוראת ביצוע
#     return [system_msg] + trimmed_history + [HumanMessage(content=execute_instruction)]


# def extract_message_by_content(messages: list, content_trigger: str, message_type: str = "ai") -> str:
#     """
#     סורקת את היסטוריית ההודעות מהסוף להתחלה ומחזירה את התוכן של ההודעה הראשונה
#     שמתאימה לסוג ולמחרוזת החיפוש.
#     """
#     for m in reversed(messages):
#         # תמיכה גם באובייקטים של LangChain וגם בדיקשנריז פשוטים
#         m_type = getattr(m, 'type', m.get('type') if isinstance(m, dict) else None)
#         m_content = getattr(m, 'content', m.get('content') if isinstance(m, dict) else "")
        
#         if m_type == message_type and content_trigger in m_content:
#             return m_content
            
#     return ""

def extract_message_by_content(messages: list, content_trigger: str, message_type: str = "ai") -> str:
    """
    סורקת את היסטוריית ההודעות מהסוף להתחלה ומחזירה את התוכן של ההודעה הראשונה
    שמתאימה לסוג, מכילה את מחרוזת החיפוש, ואינה ריקה או הודעת כלי בלבד.
    """
    for m in reversed(messages):
        # תמיכה באובייקטים של LangChain ובדיקשנריז
        m_type = getattr(m, 'type', m.get('type') if isinstance(m, dict) else None)
        m_content = getattr(m, 'content', m.get('content') if isinstance(m, dict) else "")
        
        # תמיכה במצב שבו התוכן מגיע כרשימה (קורה לפעמים ב-LangChain החדש)
        if isinstance(m_content, list):
            # מחברים את חלקי הטקסט אם יש כאלו
            m_content = " ".join([block.get("text", "") for block in m_content if isinstance(block, dict) and block.get("type") == "text"])

        # 🎯 בדיקה חסינה: לוודא שזה ה-type הנכון, שהטריגר קיים, ושזו לא הודעת אתחול ריקה של כלי
        if m_type == message_type and content_trigger in m_content:
            return m_content.strip()
            
    return ""

def get_all_processed_tool_data(messages: list, filter_func=None) -> str:
    seen_content = set()
    combined_content = []
    
    for m in messages:
        if getattr(m, 'type', '') == 'tool':
            content = m.content
            # print(f" get_all_processed_tool_data content: {content}")
            if filter_func:
                content = filter_func(content)
                # print(f" get_all_processed_tool_data content after filter: {content}")
            if content and "No reference" not in content:
                # אנחנו מחלקים לפי הכותרת אבל שומרים אותה
                chunks = content.split("--- RESULT")
                for chunk in chunks:
                    if not chunk.strip():
                        continue
                        
                    full_chunk = "--- RESULT" + chunk
                    # יצירת מזהה ייחודי ל-Chunk (בלי להתחשב ברווחים לבנים)
                    content_hash = hash(full_chunk.strip())
                    
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        combined_content.append(full_chunk.strip())
                
    return "\n\n".join(combined_content)

def filter_only_successful_tests(search_results_string: str) -> str:
    """
    מקבלת את המחרוזת המפורמטת מ-search_code ומחזירה רק chunks 
    שהם טסטים שעברו בהצלחה.
    """
    if not search_results_string or "RESULT" not in search_results_string:
        return "No reference tests found."

    # פירוק המחרוזת חזרה לתוצאות בודדות
    results = search_results_string.split("--- RESULT")
    filtered_tests = []

    for res in results:
        if not res.strip():
            continue
            
        # שיחזור ה-Header המלא לצורך בדיקה
        full_res = "--- RESULT" + res
        
        # בדיקה שה-Chunk הוא גם טסט וגם עבר (Status passed)
        # if "IS_TEST: True" in full_res and "STATUS: passed" in full_res:
        if "IS_TEST: True" in full_res:
            filtered_tests.append(full_res.strip())

    if not filtered_tests:
        return ""

    return "\n\n" + "\n\n".join(filtered_tests)
