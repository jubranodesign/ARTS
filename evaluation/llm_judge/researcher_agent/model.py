from pydantic import BaseModel, Field

class ResearcherJudgment(BaseModel):
    logic_coverage_score: int = Field(
        ge=1, le=5, 
        description="1-5: How well did the researcher explain the core technical logic?"
    )
    test_discovery_score: int = Field(
        ge=1, le=5, 
        description="1-5: Score for performing 'tests_only' search and finding golden examples."
    )
    path_integrity: bool = Field(
        description="True ONLY if full relative paths are provided for all files."
    )
    risk_alignment_score: int = Field(
        ge=1, le=5, 
        description="1-5: How well did the agent link code details to the ML Risk factors?"
    )
    forbidden_content_detected: bool = Field(
        description="True if the agent generated NEW tests/code (Forbidden!)"
    )
    reasoning: str = Field(
        description="A detailed explanation of why these scores were given, citing evidence from the dump."
    )