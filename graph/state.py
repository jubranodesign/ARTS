import operator
from typing_extensions import TypedDict 
from typing import Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # היסטוריית הודעות (נמחקת אחרי כל שלב ע"י ה-Summarizer)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    user_input: str
    # investigated_files: set[str]
#     investigated_files: Annotated[list[str], operator.add]
    # investigated_files: Annotated[set[str], operator.or_]
    # --- שדות הזיכרון (הסיכום המתגלגל) ---
    architecture_summary: str  # שלב החוקר

    test_plan: str      

    review_completed: bool
           # שלב המעצב
    target_file: str           # הנתיב לקובץ המקורי
 
    # # --- שלב הכותב (Writer) ---
    test_file_path: str        # הנתיב לקובץ שנוצר (למשל: tests/test_api.py)
    
    # # --- שלב המריץ (Runner) - כאן זה נמצא! ---
    # # סטטוס הריצה: האם הטסט עבר או נכשל
    test_run_status: Literal["passed", "failed", "pending"] 
    
    # # הלוג המלא של pytest (כדי שהמעצב יוכל לתקן אם נכשל)
    last_run_logs: str

    test_chunks: str

    attempts: int

    risk_score: float

    risk_reasons: list[dict] 

    target_file_code: str

    golden_test_summary: str