# agents/researcher/logic_nodes.py
import re
from graph.state import AgentState

def update_investigated_files(state: AgentState):
    messages = state.get("messages", [])
    
    # אנחנו צריכים לפחות 2 הודעות: הבקשה והתשובה מהכלי
    if len(messages) < 2:
        return {"investigated_files": []}

    last_msg = messages[-1]  # הודעת ה-Tool
    prev_msg = messages[-2]  # הודעת ה-AI שביקשה את הכלי

    # בדיקה שהכלי הצליח ושזו אכן הודעת Tool
    if last_msg.type == "tool" and "SUCCESS" in (last_msg.content or ""):
        # חילוץ הנתיב מה-tool_calls של ההודעה הקודמת
        if hasattr(prev_msg, 'tool_calls') and prev_msg.tool_calls:
            # כאן התיקון הקריטי: מחפשים 'file_path' במקום 'path'
            found_path = prev_msg.tool_calls[0]['args'].get('file_path')
            
            if found_path:
                already_seen = state.get("investigated_files", [])
                if found_path not in already_seen:
                    print(f"✅ SUCCESSFULLY ADDED: {found_path}")
                    return {"investigated_files": [found_path]}
    
    return {"investigated_files": []}