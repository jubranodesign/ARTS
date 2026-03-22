from typing import List

from pydantic import BaseModel, Field

# class ArchitectureSnapshot(BaseModel):
#     """
#     סכימה מובנית לסיכום הארכיטקטורה של הפרויקט.
#     משמשת את ה-Summarizer להחזרת פלט נקי ומאורגן.
#     """
#     summary: str = Field(
#         description="A concise technical description of the architecture. Use simple text, avoid complex nested markdown."
#         # description="The full technical summary of the system architecture in Markdown format."
#     )
#     last_updated_component: str = Field(
#         description="The specific component or folder that was most recently analyzed (e.g., '/api/routes')."
#     )
#     confidence_score: float = Field(
#         description="A score between 0 and 1 representing how confident the architect is in this summary."
#     )

# class ArchitectureSnapshot(BaseModel):
#     """
#     סכימה מובנית ומפורקת למניעת שגיאות 400 ב-Groq.
#     """
#     component_name: str = Field(description="The logical name of the module (e.g., Scraper API)")
#     source_file: str = Field(description="The relative path to the file")
#     logic: str = Field(description="Brief technical description of what the code does")
#     key_elements: list[str] = Field(description="List of main functions and classes found")
#     dependencies: list[str] = Field(description="List of imported libraries (e.g., requests, flask)")
#     confidence_score: float = Field(description="Confidence score between 0 and 1")


class ArchitectureSnapshot(BaseModel):
    """
    סכימה משולבת: גם שדות טכניים מפורקים וגם סיכום מילולי של הקובץ.
    מבנה זה מונע שגיאות 400 ב-Groq כי הוא מגדיר ציפיות ברורות ל-LLM.
    """
    component_name: str = Field(
        description="The logical name of the module or service."
    )
    source_file: str = Field(
        description="The relative path to the source file analyzed."
    )
    file_summary: str = Field(
        description="A clear, high-level prose description of what this file does and its role in the system."
    )
    logic: str = Field(
        description="Technical details about how the functions/logic are implemented."
    )
    key_elements: List[str] = Field(
        description="A list of the main functions, classes, or constants identified."
    )
    dependencies: List[str] = Field(
        description="List of external and internal imports (e.g., requests, os, shared_utils)."
    )
    confidence_score: float = Field(
        description="Confidence level in this analysis (0.0 to 1.0)."
    )

    def to_summary_text(self) -> str:
        """Human-readable block for state['architecture_summary'] (Designer / Writer)."""
        key_el = (
            ", ".join(self.key_elements)
            if isinstance(self.key_elements, list)
            else self.key_elements
        )
        deps = (
            ", ".join(self.dependencies)
            if isinstance(self.dependencies, list)
            else self.dependencies
        )
        return f"""Component: {self.component_name}
File: {self.source_file}
General Description: {self.file_summary}
Technical Logic: {self.logic}
Key Elements: {key_el}
Dependencies: {deps}
"""