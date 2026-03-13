from pydantic import BaseModel, Field

class ArchitectureSnapshot(BaseModel):
    """
    סכימה מובנית לסיכום הארכיטקטורה של הפרויקט.
    משמשת את ה-Summarizer להחזרת פלט נקי ומאורגן.
    """
    summary: str = Field(
        description="A concise technical description of the architecture. Use simple text, avoid complex nested markdown."
        # description="The full technical summary of the system architecture in Markdown format."
    )
    last_updated_component: str = Field(
        description="The specific component or folder that was most recently analyzed (e.g., '/api/routes')."
    )
    confidence_score: float = Field(
        description="A score between 0 and 1 representing how confident the architect is in this summary."
    )