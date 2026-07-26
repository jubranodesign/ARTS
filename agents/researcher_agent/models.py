from typing import List, Optional

from pydantic import BaseModel, Field


class ArchitectureSnapshot(BaseModel):
    component_name: str = Field(description="The logical name of the module or service.")
    source_file: str = Field(description="The relative path to the source file analyzed.")
    file_summary: str = Field(description="A clear, high-level prose description.")
    logic: str = Field(description="Technical details about functions/logic.")
    risk_profile: str = Field(
        default="Not Analyzed", 
        description="Summary of ML Risk score and specific architectural concerns found."
    )
    key_elements: List[str] = Field(description="Main functions, classes, or constants.")
    dependencies: List[str] = Field(description="List of imports.")
   

    test_pattern: Optional[str] = Field(
        default=None,
        description="EXACTLY ONE high-quality 'Golden Example' of a passing test found in research. "
                    "Includes essential imports and mocker.patch path. If no tests found, return None."
    )
    
    confidence_score: float = Field(description="Confidence level (0.0 to 1.0).")

    def to_summary_text(self) -> str:
        """מעדכן את הייצוג הטקסטואלי שהכותב רואה"""
        key_el = ", ".join(self.key_elements) if isinstance(self.key_elements, list) else self.key_elements
        deps = ", ".join(self.dependencies) if isinstance(self.dependencies, list) else self.dependencies
        
        # בניית הבלוק הבסיסי
        summary = f"""Component: {self.component_name}
File: {self.source_file}
General Description: {self.file_summary}
Technical Logic: {self.logic}
Risk Profile: {self.risk_profile}
Key Elements: {key_el}
Dependencies: {deps}
"""
        # הוספת ה-Golden Example רק אם הוא קיים
        if self.test_pattern and self.test_pattern.lower() != "none":
            summary += f"\n--- REFERENCE TEST PATTERN (Golden Example) ---\n{self.test_pattern}\n"
            
        return summary
