from shared.llm_factory import get_model  # או כל פרוויידר אחר שאתה עובד איתו

# 1. הגדרת קוד המקור של הניסוי כמחרוזת
TEST_SOURCE_CODE = """
import requests

API_URL = "https://clinicaltrials.gov/api/v2/studies"


def fetch_studies(page_size: int = 5) -> list[dict]:
    params = {"pageSize": page_size, "format": "json"}
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json().get("studies", [])
"""


DESIGNER_PROMPT_TEMPLATE = """
### ROLE:
You are a Senior Backend Developer and Testing Architect. Your goal is to design a robust testing strategy (Test Plan) for the provided source code.

### CONTEXT:
--- SOURCE CODE TO TEST ---
{source_code}

### USER REQUEST:
The developer wants to: "{user_input}"

### ⛔ STRICT SOURCE ADHERENCE (ANTI-HALLUCINATION):
- **ONLY TEST WHAT EXISTS:** You MUST generate test cases ONLY for the functions and logic present in the provided source code.
- **NO ASSUMPTIONS:** If you don't see an import or library used in the code, DO NOT assume it exists.
- **PARAMETER CHECK:** Cross-reference function signatures. For example, if `fetch_studies` takes `page_size`, test its behavior around this parameter specifically.
- **LIMIT:** Generate a maximum of 4 high-impact test cases. Avoid bloating the plan with redundant scenarios.

### TASK:
1. Analyze the core logic and dependencies of the provided function.
2. Identify potential edge cases and failure points (e.g., API timeouts, HTTP errors, empty JSON payloads).
3. Create a structured Test Plan in Markdown.

### ⛔ STRICT RULES (NO CODE):
- **DO NOT WRITE ANY ACTUAL TEST CODE.** No Python code blocks.
- Focus ONLY on the **Logic, Strategy, and Mocks**.

### TEST PLAN STRUCTURE (MANDATORY):
1. **Goal:** Brief summary of what we are testing.
2. **Test Cases**: 
   Provide a numbered list of all scenarios starting from 1. 
   (Format: 1. **[Scenario Name]**: [Short description])
3. **Logic Per Case:** For each case, describe the exact steps and the expected result in plain English.
4. **Mocks & Setup:** Define exactly what external services must be mocked (e.g., `requests.get`) and what they should return (e.g., 200 OK with specific JSON, or a 500 Server Error).

### GUIDELINES:
- Focus on real-world reliability: Success path, Empty Response, API Error (4xx/5xx), and Network Timeout.
"""

APPROVED_PLAN = """
1. **[Success Path]**: Fetch studies with a valid response.
2. **[Empty Response]**: Handle an API response with no studies.
3. **[HTTP Error]**: Simulate a 4xx/5xx error from the API.
4. **[Network Timeout]**: Simulate a timeout when calling the API.
"""

WRITER_PROMPT_TEMPLATE = """
### ROLE:
You are a Senior Python Developer and QA Automation Expert.
Your goal is to transform the provided Approved Test Plan into executable Pytest code that accurately tests the provided SOURCE CODE.

### CONTEXT:
- Target Function: fetch_studies
- Import Path: scraper_service.scraper_api  # (הנתיב הלוגי לצורך ה-mocker.patch)
- Test Framework: pytest
- Mocking Tool: pytest-mock (mocker fixture)

### 📚 KNOWLEDGE BASE:
#### 💡 REFERENCE MOCK PATTERN:
{golden_example}
NOTE: This is an example of STYLE only. If it is "None", write standard idiomatic pytest code using the `mocker` fixture.

### WORKFLOW RULES:
1. **SOURCE FIDELITY (CRITICAL)**: Review the ACTUAL `SOURCE CODE` provided below. Your tests must align 100% with its exact logic.
   - If the code does NOT catch an exception (e.g., `response.raise_for_status()`), the test MUST expect the exception to raise using `with pytest.raises(...)`.
   - DO NOT invent or assume behavior (like timeouts or retries) if they are not explicitly written in the source code.
2. **STRICT ALIGNMENT**: Implement EXACTLY the test cases described in the Approved Test Plan.
3. **NO REASONING**: Just generate the raw Python code. Do not explain, do not add introductory or concluding text.
4. **NO FIXTURES**: Put all mocks, setups, execution, and assertions inside each test function body.

### ⛔ IMPORT & PATCHING RULES (STRICT ENFORCEMENT):
1. **MANDATORY BOILERPLATE ORDER**:
   Your code MUST follow this exact sequence to prevent import errors:
   a) `import sys` and `from unittest.mock import MagicMock` (if needed for complex structures).
   b) `import pytest, requests`.
   c) Import the target function.

2. **LOCAL VARIABLE MOCKING (MANDATORY)**:
   - ALWAYS capture every patch in a local variable: e.g., `mock_get = mocker.patch(...)`.
   - Use that local variable ONLY for assertions: `mock_get.assert_called_once()`.
   - **FORBIDDEN**: Do not use global module names in assertions.

3. **SMART PATCHING PATHS**:
   - ALWAYS patch objects where they are USED in the target file.
   - Since the target function uses `requests.get`, patch it where it is used: `mocker.patch('scraper_service.scraper_api.requests.get')`.

⛔ **CRITICALLY REALISTIC ASSERTIONS**:
- Read the source code carefully: If there is no `try-except` around `requests.get`, then an HTTP error or Timeout WILL bubble up. Ensure your test expects this behavior.
- Name your functions clearly: `test_fetch_studies_success`, `test_fetch_studies_timeout`, etc.

---
### SOURCE CODE TO TEST:
{source_code}

### APPROVED TEST PLAN:
{plan}

FINAL INSTRUCTION:
Implement all test cases from the plan now as clean, executable Python code.
"""


def run_designer_experiment():
    # 2. אתחול המודל (למשל GPT-4o או מודל אחר מהקונפיגורציה שלך)
    llm = get_model("mistral")

    # 3. הגדרת המשימה של המשתמש
    user_input = "Write comprehensive unit tests for the fetch_studies function covering network resilience."

    # 4. בניית הפרומפט והזרקת המשתנים (הקוד והמשימה)
    prompt_text = DESIGNER_PROMPT_TEMPLATE.format(
        source_code=TEST_SOURCE_CODE,
        user_input=user_input,
    )

    print("🚀 Sending tailored prompt to Designer LLM...")
    print("-" * 50)

    # 5. הרצת המודל
    response = llm.invoke(prompt_text)

    # 6. הצגת תוכנית הבדיקות (Test Plan) שהתקבלה
    print("\n📊 --- GENERATED TEST PLAN ---")
    print(response.content)


def run_writer_experiment():
    # אתחול המודל (על Temperature נמוך מאוד בשביל קוד דטרמיניסטי)
    llm = get_model("mistral")

    # נניח שאין לנו Golden Example בריצה הזו
    golden_example = "None"

    # הזרקת הנתונים לפרומפט המעודכן
    prompt_text = WRITER_PROMPT_TEMPLATE.format(
        source_code=TEST_SOURCE_CODE,
        plan=APPROVED_PLAN,
        golden_example=golden_example,
    )

    print("🚀 Sending tailored prompt to Writer LLM...")
    print("-" * 50)

    # הרצת המודל
    response = llm.invoke(prompt_text)

    print("\n🐍 --- GENERATED PYTEST CODE ---")
    print(response.content)


if __name__ == "__main__":
    run_writer_experiment()