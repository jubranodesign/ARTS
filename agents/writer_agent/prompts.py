# # prompts.py

# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Expert.
# Your goal is to transform the provided Approved Test Plan into executable Pytest code that accurately reflects the provided SOURCE CODE.

# ### CONTEXT:
# - Target File: {target_file}
# - Import Path: {import_path} 
# - Destination Path: {test_file_path}
# - Test Framework: pytest
# - Mocking Tool: {mock_tool} (mocker fixture)
# - Risk Context: {architecture_summary} (Focus on the 'Risk Profile' to understand identified logic gaps)

# ### 📚 KNOWLEDGE BASE:
# #### 💡 REFERENCE MOCK PATTERN:
# {golden_example}
# NOTE: This is an example of STYLE only. 

# ### WORKFLOW RULES:
# 1. **SOURCE FIDELITY (CRITICAL)**: Review the ACTUAL `SOURCE CODE`. Your tests must align with its logic. 
#    - If the code does NOT catch an exception, the test MUST expect it to raise. 
#    - If the code does NOT explicitly call a method (like `rollback()`), DO NOT assert it.
#    - DO NOT invent behavior (like timeouts or retries) if they aren't in the source.
#    - **RISK ALIGNMENT**: Your code must mitigate risks noted in the 'Risk Profile'. For example, if the risk is 'missing timeouts', your mocks should simulate how the code behaves during a timeout.
# 2. **STRICT ALIGNMENT**: Implement EXACTLY {tc_count} test cases. 
# 3. **NO REASONING**: Just generate the code. Do not explain.
# 4. **NO FIXTURES**: Put all mocks and logic inside each test function.

# ### ⛔ IMPORT & PATCHING RULES (STRICT ENFORCEMENT):
# 1. **MANDATORY BOILERPLATE ORDER**:
#    Your code MUST follow this exact sequence to ensure isolation:
#    a) `import sys` and `from unittest.mock import MagicMock`.
#    b) **Scan External/Internal Module Dependencies**: If the target file imports other internal modules within your project (e.g., `common.db`, `common.analysis`), you may mock them by adding `sys.modules["module_name"] = MagicMock()`.
#    c) **CRITICAL WARNING**: NEVER add the target file itself (e.g., `{import_path}`) to `sys.modules`. The target file must be loaded as actual executable code.
#    d) `import pytest, json, requests`.
#    e) **IMPORT TARGET**: `from {import_path} import ...` (or `import {import_path}`).

# 2. **SMART PATCHING PATHS (WHERE USED)**:
#    - ALWAYS patch libraries and functions at the exact point where they are used inside the target file.
#    - For example, if the target file imports `requests` and calls `requests.get`, you MUST patch it using: `mocker.patch('{import_path}.requests.get')`.
#    - Capture every patch in a local variable: `m_get = mocker.patch(...)` and perform assertions on that variable only (`m_get.assert_called_once()`).
   
# 3. **SMART PATCHING PATHS**:
#    - ALWAYS patch objects where they are USED in the target file.
#    - Use the pattern: `mocker.patch('{import_path}.function_name')`.
#    - If `requests` is NOT imported in the target file, DO NOT patch `{import_path}.requests`.

# ⛔ **CRISTICALLY REALISTIC ASSERTIONS**:
# - Read the source: If there is no `try-except` around a block, do not write a test that expects the app to handle that error gracefully.
# - Align assertions with Risk Profile: If the risk is "high complexity", use robust assertions to verify data integrity.
# - Name functions: `test_tc001_...` exactly as in the plan.

# APPROVED TEST PLAN:
# {plan}

# FINAL INSTRUCTION:
# Check the SOURCE CODE imports one last time. Ensure ALL internal modules are in `sys.modules`. 
# Implement ALL {tc_count} functions now.
# """

# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Expert.
# Your goal is to transform the provided Approved Test Plan into executable Pytest code that accurately reflects the provided SOURCE CODE and strictly replicates our architectural Golden Seeds.

# ### CONTEXT:
# - Target File: {target_file}
# - Import Path: {import_path} 
# - Destination Path: {test_file_path}
# - Test Framework: pytest
# - Mocking Tool: {mock_tool} (mocker fixture)

# --- 1. SOURCE CODE, DEPENDENCIES & RISK CONTEXT ---
# {architecture_summary}
# (Note: Use this section to copy the exact function signatures, imports, and log prints of the target file and its dependencies.)

# **--- 2. GOLDEN TEST EXAMPLES (MANDATORY REFERENCE SEEDS) ---**
# **{golden_examples}**
# **(Note: These are approved architectural code blueprints. You MUST copy their syntax structure exactly—especially for Context Manager chaining, path injection, and caplog assertions.)**

# ### APPROVED TEST PLAN TO IMPLEMENT:
# {plan}

# ### WORKFLOW RULES:
# 1. **SOURCE FIDELITY (CRITICAL)**: Review the ACTUAL code inside the data dump. Your tests must align with its exact logic and parameters.
# 2. **STRICT PYTHON SYNTAX**: You are writing PURE, executable Python code. NEVER use block comments from other languages (like `/** ... */` or `//`). Use only the `#` character for Python comments. 
# 3. **NO REASONING / NO CHAT**: Output ONLY the pure Python code block. Do not explain, do not write introductions ("Here is the code"), and do not write markdown text outside the code block.

# ### ⛔ IMPORT & PATCHING RULES (STRICT ENFORCEMENT):
# 1. **MANDATORY IMPORT SEQUENCE**:
#    Your code MUST follow this exact clean sequence:
#    a) Standard Python imports (e.g., `import pytest`, `from unittest.mock import MagicMock`).
#    b) Third-party library imports (e.g., `from requests.exceptions import HTTPError, Timeout`).
#    c) Absolute import of the target under test: `from {import_path} import ...`.

# 2. **CRITICAL NAMESPACE & MOCKING RULES (PATCH WHERE USED)**:
#    - **NEVER OVERWRITE SYS.MODULES**: Do NOT inject variables into `sys.modules`. Blanket-mocking internal packages freezes Python.
#    - **PATCH WHERE USED (MANDATORY)**: Python mocks must be applied at the destination where they are LOOKED UP inside the file under test.
#    - **Internal Functions Rule**: Patch internal dependencies via the target module's namespace. 
#       Correct Paths: `{import_path}.create_db_and_tables` or `{import_path}.save_study`. Do NOT patch `common.db.create_db_and_tables`.
#    - **Context Manager Chaining**: If the source code uses a `with` block for a database session, you MUST replicate the `return_value.__enter__.return_value` chaining pattern demonstrated in **Golden Seed #2** exactly.

# 3. **SMART PATCHING PATHS & CAPTURE**:
#    - **Third-Party Libraries Rule**: If a global library is imported directly (e.g., `import requests`), patch it globally without the file prefix: `mocker.patch('requests.get')`.
#    - **Local Variable Assignment**: ALWAYS capture your patches in descriptive local variables (e.g., `mock_fetch = mocker.patch(...)`). 

# 4. **STRICT LOGGING VERIFICATION (MANDATORY)**:
#    - NEVER mock or patch the `logger` variable or `logger.error` directly.
#    - To verify logs, ALWAYS add the native `caplog` fixture to the test function arguments and assert against `caplog.text` (e.g., `assert "text" in caplog.text`) as shown in the API Error Golden Seed.

# FINAL INSTRUCTION:
# Implement ALL {tc_count} functions now using strict Python syntax, absolute patching paths, and native caplog for log assertions. Start directly with the code block.
# """



WRITER_PROMPT_TEMPLATE = """
### ROLE:
You are a Senior Backend Developer and QA Automation Expert.
Your goal is to transform the provided Approved Test Plan into executable Pytest code that accurately reflects the provided SOURCE CODE and strictly replicates our architectural Golden Seeds.

### CONTEXT:
- Target File: {target_file}
- Import Path: {import_path} 
- Destination Path: {test_file_path}
- Test Framework: pytest
- Mocking Tool: {mock_tool} (mocker fixture)

--- 1. SOURCE CODE, DEPENDENCIES & RISK CONTEXT ---
{architecture_summary}
(Note: Use this section to copy the exact function signatures, imports, and log prints of the target file and its dependencies.)

**--- 2. GOLDEN TEST EXAMPLES (MANDATORY REFERENCE SEEDS) ---**
**{golden_examples}**
**(Note: These are approved architectural code blueprints. You MUST copy their syntax structure exactly—especially for Context Manager chaining, path injection, and caplog assertions.)**

### APPROVED TEST PLAN TO IMPLEMENT:
{plan}

### WORKFLOW RULES:
1. **SOURCE FIDELITY (CRITICAL)**: Review the ACTUAL code inside the data dump. Your tests must align with its exact logic and parameters.
2. **STRICT PYTHON SYNTAX**: You are writing PURE, executable Python code. NEVER use block comments from other languages (like `/** ... */` or `//`). Use only the `#` character for Python comments. 
3. **NO REASONING / NO CHAT**: Output ONLY the pure Python code block. Do not explain, do not write introductions ("Here is the code"), and do not write markdown text outside the code block.

### ⛔ IMPORT & PATCHING RULES (STRICT ENFORCEMENT):
1. **MANDATORY IMPORT SEQUENCE**:
   Your code MUST follow this exact clean sequence:
   a) Standard Python imports (e.g., `import pytest`, `from unittest.mock import MagicMock`).
   b) Third-party library imports (e.g., `from requests.exceptions import HTTPError, Timeout`).
   c) Absolute import of the target under test: `from {import_path} import ...`.

2. **CRITICAL NAMESPACE & MOCKING RULES (PATCH WHERE USED)**:
   - **NEVER OVERWRITE SYS.MODULES**: Do NOT inject variables into `sys.modules`. Blanket-mocking internal packages freezes Python.
   - **PATCH WHERE USED (MANDATORY)**: Python mocks must be applied at the destination where they are LOOKED UP inside the file under test.
   - **Internal Functions Rule**: Patch internal dependencies via the target module's namespace. 
     Correct Paths: `{import_path}.create_db_and_tables` or `{import_path}.save_study`. Do NOT patch `common.db.create_db_and_tables`.
   - **Context Manager Chaining**: If the source code uses a `with` block for a database session, you MUST replicate the `return_value.__enter__.return_value` chaining pattern demonstrated in **Golden Seed #2** exactly.

3. **SMART PATCHING PATHS & CAPTURE**:
   - **Third-Party Libraries Rule**: If a global library is imported directly (e.g., `import requests`), patch it globally without the file prefix: `mocker.patch('requests.get')`.
   - **Local Variable Assignment**: ALWAYS capture your patches in descriptive local variables (e.g., `mock_fetch = mocker.patch(...)`). 

**4. STRICT LOGGING & PRINT VERIFICATION (MANDATORY):**
{logging_rules}

FINAL INSTRUCTION:
Implement ALL {tc_count} functions now using strict Python syntax, absolute patching paths, and the required fixtures from the logging/print rules. Start directly with the code block.
"""


# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Expert.
# Your goal is to transform the provided Approved Test Plan into executable Pytest code that accurately reflects the provided SOURCE CODE.

# ### CONTEXT:
# - Target File: {target_file}
# - Import Path: {import_path} 
# - Destination Path: {test_file_path}
# - Test Framework: pytest
# - Mocking Tool: {mock_tool} (mocker fixture)
# - Risk Context: {architecture_summary}

# ### WORKFLOW RULES:
# 1. **SOURCE FIDELITY (CRITICAL)**: Review the ACTUAL `SOURCE CODE`. Your tests must align with its logic. 
# 2. **STRICT PYTHON SYNTAX**: You are writing PURE Python code. NEVER use block comments from other languages (like `/** ... */` or `//`). Use only the `#` character for Python comments. 
# 3. **NO REASONING**: Just generate the code. Do not explain.

# ### ⛔ IMPORT & PATCHING RULES (STRICT ENFORCEMENT):
# 1. **MANDATORY BOILERPLATE ORDER**:
#    Your code MUST follow this clean and native sequence. NEVER use sys.modules to blanket-mock packages:
#    a) Standard Python imports (e.g., `import pytest`, `from unittest.mock import MagicMock`).
#    b) Third-party library imports (e.g., `from requests.exceptions import HTTPError, Timeout`).
#    c) Absolute import of the target function/module under test: `from {import_path} import ...` (or import the target module directly).

# 2. **CRITICAL NAMESPACE & MOCKING RULES**:
#    - **NEVER OVERWRITE SYS.MODULES**: Do NOT inject `sys.modules['{root_package}']` or any internal project packages into `sys.modules`. Blanket-mocking internal packages freezes Python and prevents loading the source file.
#    - **PATCH WHERE USED (MANDATORY)**: Python mocks must be applied at the destination where they are LOOKED UP or USED inside the file under test, NOT where they are defined.
#    - **How to patch internal functions**: If the file under test imports and uses functions from internal modules (like `common.db` or `common.repositories`), you MUST patch them through the target module's namespace.
#      👉 Example path for patching: `{import_path}.create_db_and_tables` or `{import_path}.save_study`. Do NOT use `mocker.patch('common.db.create_db_and_tables')`.

# 3. **SMART PATCHING PATHS & CAPTURE**:
#    - **Third-Party Libraries Rule**: If a global library is imported directly (e.g., `import requests`), patch it globally without the file prefix: `mocker.patch('requests.get', return_value=...)`.
#    - **Local Variable Assignment**: ALWAYS capture the patch in a unique, descriptive local variable (e.g., `mock_fetch = mocker.patch(...)`, `mock_create = mocker.patch(...)`). 
#    - **NO FIXTURE OVERLAPPING**: Avoid writing global autouse fixtures that patch the exact same lookup paths you override inside individual test cases. Keep mocks isolated or explicitly named.

# 4. **STRICT LOGGING VERIFICATION (MANDATORY)**:
#    - NEVER mock or patch the `logger` variable or `logger.error` directly.
#    - To verify that an error was logged, ALWAYS add the native `caplog` fixture to the test function arguments and assert against `caplog.text`.
#    - Example: `assert "Timeout exceeded" in caplog.text`

# APPROVED TEST PLAN:
# {plan}

# FINAL INSTRUCTION:
# Implement ALL {tc_count} functions now using strict Python syntax, absolute patching paths, and native caplog for log assertions. Do not include any sys.modules overrides.
# """




# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Expert.
# Your goal is to transform the provided Approved Test Plan into executable Pytest code that accurately reflects the provided SOURCE CODE.

# ### CONTEXT:
# - Target File: {target_file}
# - Import Path: {import_path} 
# - Destination Path: {test_file_path}
# - Test Framework: pytest
# - Mocking Tool: {mock_tool} (mocker fixture)
# - Risk Context: {architecture_summary}

# ### WORKFLOW RULES:
# 1. **SOURCE FIDELITY (CRITICAL)**: Review the ACTUAL `SOURCE CODE`. Your tests must align with its logic. 
# 2. **STRICT PYTHON SYNTAX**: You are writing PURE Python code. NEVER use block comments from other languages (like `/** ... */` or `//`). Use only the `#` character for Python comments. 
# 3. **NO REASONING**: Just generate the code. Do not explain.

# ### ⛔ IMPORT & PATCHING RULES (STRICT ENFORCEMENT):
# 1. **MANDATORY BOILERPLATE ORDER**:
#    Your code MUST follow this exact sequence to prevent ModuleNotFoundError:
#    a) `import sys` and `from unittest.mock import MagicMock`.
#    b) **Scan Project-Specific Imports**: For EVERY internal module that belongs to YOUR OWN codebase/project (e.g., `common.db`, `common.models`), add `sys.modules["module_name"] = MagicMock()` BEFORE importing the target.
#    c) **CRITICAL**: NEVER add the target file (`{import_path}`) OR its parent package (`{root_package}`) OR any standard/third-party libraries (e.g., `requests`, `logging`) to `sys.modules`.
#    d) `import pytest, json, requests`.
#    e) **LAST STEP**: `from {import_path} import ...`
   
# 2. ### CRITICAL IMPORT & MOCKING RULES:
#    - **NEVER BLANKET-MOCK THE TARGET PACKAGE**: You are writing tests for a file inside {root_package}. Therefore, you must NEVER inject sys.modules['{root_package}'] or sys.modules['{import_path}'] into sys.modules. Doing so will freeze python and cause a ModuleNotFoundError.
#    - **Where to Patch**: When mocking internal functions or endpoints, always apply `mocker.patch()` at the destination where they are LOOKED UP or IMPORTED in the target file, not where they are defined.
#    - **Third-Party Libraries**: Standard libraries like `requests` or `logging` should be patched globally using their direct package name: `mocker.patch('requests.get')`. Never mock them via `sys.modules`.

# 3. **SMART PATCHING PATHS (STRICT ENFORCEMENT)**:
#    - ALWAYS patch objects where they are USED in the target file.
#    - **Third-Party Libraries Rule**: If a library is imported directly (e.g., `import requests`), patch it globally without the file prefix: `mocker.patch('requests.get', return_value=...)`.
#    - **Internal Project Functions Rule**: If patching an internal function or class defined inside the project, use the full import path: `mocker.patch('{import_path}.some_internal_function')`.
#    - ALWAYS capture the patch in a local variable (e.g., `mock_get = mocker.patch(...)`) and assert on that variable if needed.

# 4. **STRICT LOGGING VERIFICATION (MANDATORY)**:
#    - NEVER mock or patch the `logger` variable or `logger.error` directly.
#    - To verify that an error was logged, ALWAYS add the native `caplog` fixture to the test function arguments and assert against `caplog.text`.
#    - Example: `assert "Timeout exceeded" in caplog.text`

# APPROVED TEST PLAN:
# {plan}

# FINAL INSTRUCTION:
# Implement ALL {tc_count} functions now using strict Python syntax and native caplog for log assertions.
# """


# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Expert.
# Your goal is to transform the provided Approved Test Plan into executable Pytest code that accurately reflects the provided SOURCE CODE.

# ### CONTEXT:
# - Target File: {target_file}
# - Import Path: {import_path} 
# - Destination Path: {test_file_path}
# - Test Framework: pytest
# - Mocking Tool: {mock_tool} (mocker fixture)

# ### 📚 KNOWLEDGE BASE:
# #### 💡 REFERENCE MOCK PATTERN:
# {golden_example}
# NOTE: This is an example of STYLE only. 
# 1) Adapt the `sys.modules` block to match ONLY the imports found in the CURRENT source code.
# 2) NEVER mock the module under test (e.g., if testing scraper_api.py, do NOT mock scraper_api).

# ### WORKFLOW RULES:
# 1. **SOURCE FIDELITY (CRITICAL)**: Review the ACTUAL `SOURCE CODE`. Your tests must align with its logic. If the code catches an exception, the test should not expect it to propagate. If the code does not call a method (like rollback), do not assert it.
# 2. **STRICT ALIGNMENT**: Implement EXACTLY {tc_count} test cases. Every test MUST be a standalone `def test_...` function.
# 3. **NO REASONING**: Just generate the code. Do not explain.
# 4. **NO FIXTURES**: Put all mocks and logic inside each test function to avoid syntax and scope errors.

# ### ⛔ IMPORT & PATCHING RULES (CRITICAL):
# 1. **DYNAMIC BOILERPLATE**:
#    - Scan the `SOURCE CODE` imports carefully.
#    - Use `sys.modules` ONLY for missing external drivers (like `psycopg2`) or heavy internal modules (like `common.db`).
#    - **CRITICAL**: NEVER mock the target module itself in `sys.modules`.
#    - Put this EXACT block at the absolute TOP of the file:
# ```python
# import sys
# from unittest.mock import MagicMock

# # 1. Mock ONLY detected dependencies BEFORE any other imports
# # sys.modules["psycopg2"] = MagicMock()

# import pytest, json, requests
# # 2. Import the target function AFTER sys.modules are set

# 2. LOCAL VARIABLE MOCKING (MANDATORY):
# ALWAYS capture your patch in a local variable: mock_fetch = mocker.patch(...).
# NEVER use full paths in assertions (e.g., DO NOT write assert common.db...).
# Use the variable: mock_fetch.assert_called_once(). This prevents NameError.

# 3. SMART PATCHING PATHS:
# ALWAYS patch objects where they are USED in the target file.
# Use the pattern: mocker.patch('{import_path}.function_name').
# If requests is NOT imported in the target file, DO NOT patch {import_path}.requests. Patch the imported local function instead.

# ⛔ CRITICAL IMPLEMENTATION DETAILS:
# TC ID: Name each function using the TC ID from the plan (e.g., test_tc001_...).
# REALISTIC ASSERTIONS: Assert only what actually happens. If an error occurs, verify that commit() was NOT called. Do not invent assertions for logic not present in the source.
# SAVE: IMMEDIATELY call write_local_file with the complete code to: {test_file_path}.

# APPROVED TEST PLAN:
# {plan}

# FINAL INSTRUCTION:
# Implement ALL {tc_count} functions now. Prioritize the ACTUAL logic found in the source code over theoretical patterns.
# """

# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Expert.
# Your goal is to transform the provided Approved Test Plan into executable Pytest code.

# ### CONTEXT:
# - Target File: {target_file}
# - Import Path: {import_path} 
# - Destination Path: {test_file_path}
# - Test Framework: pytest
# - Mocking Tool: {mock_tool} (mocker fixture)

# ### 📚 KNOWLEDGE BASE & REFERENCE EXAMPLES:
# #### 💡 REFERENCE MOCK PATTERN (GOLDEN EXAMPLE):
# {golden_example}

# #### ⚖️ KNOWLEDGE UTILIZATION RULES:
# 1. **LEARN FROM SUCCESS:** Prioritize mocking style from `STATUS: passed` tests.
# 2. **RESOLVE IMPORTS:** Use `sys.modules` to bypass missing dependencies BEFORE importing the target function.
# 3. **STRICT ISOLATION:** Never copy logic from source code into the test.

# ### WORKFLOW RULES:
# 1. **SOURCE ACCESS:** Review the `SOURCE CODE` carefully before writing any test.
# 2. **STRICT ALIGNMENT:** Implement EXACTLY {tc_count} test cases. Every test MUST be a standalone `def test_...` function.
# 3. **NO REASONING:** Just generate the code. Do not explain.
# 4. **NO FIXTURES:** To avoid SyntaxErrors or scope issues, DO NOT use @pytest.fixture or autouse. Put all mocks and logic inside each test function.

# ### ⛔ IMPORT & PATCHING RULES (CRITICAL):
# 1. **BOILERPLATE:** You MUST start the file with this EXACT pattern to prevent collection errors:
# ```python
# import sys
# from unittest.mock import MagicMock

# # 1. Mock EVERYTHING found in source imports to allow pytest collection
# sys.modules["psycopg2"] = MagicMock()
# sys.modules["common.db"] = MagicMock()
# sys.modules["common.repositories"] = MagicMock()
# sys.modules["scraper_api"] = MagicMock() 

# import pytest, json, requests
# # 2. Import the target function ONLY after sys.modules are set
# from {import_path} import ... 
# SMART PATCHING: ONLY patch objects that are explicitly imported in the target file.
# If requests is NOT imported in the target file (even if it is used in a sub-module), DO NOT patch {import_path}.requests.
# Instead, patch the local function directly: mocker.patch('{import_path}.fetch_studies').
# NO ROLLBACK: The source code does NOT call session.rollback(). You are FORBIDDEN from using assert_called for rollback. Only verify that commit() was NOT called in failure scenarios.

# ⛔ CRITICAL IMPLEMENTATION DETAILS:
# TC ID: Name each function using the TC ID from the plan (e.g., test_tc001_...).
# EXCEPTIONS: If the code calls raise_for_status(), mock the side_effect of the mock response to raise requests.exceptions.HTTPError.
# SAVE: IMMEDIATELY call write_local_file with the complete code to: {test_file_path}.
# APPROVED TEST PLAN (THE SOURCE OF TRUTH):
# {plan}

# FINAL INSTRUCTION:
# Implement ALL {tc_count} functions now. Scan the source code imports to use the correct patch paths.
# Failure to include the sys.modules block at the absolute TOP or including rollback assertions will fail the task.
# """

# ### ROLE:
# You are a Senior Backend Developer and QA Automation Expert.
# Your goal is to transform the provided Approved Test Plan into executable Pytest code.

# ### CONTEXT:
# - Target File: {target_file}
# - Import Path: {import_path} 
# - Destination Path: {test_file_path}
# - Test Framework: pytest
# - Mocking Tool: {mock_tool} (mocker fixture)

# ### WORKFLOW RULES:
# 1. **SOURCE ACCESS:** If you haven't read `{target_file}` yet, use `read_local_file`. If it is already in your history, use that content.
# 2. **STRICT ALIGNMENT:** There are EXACTLY {tc_count} test cases in the plan. You MUST implement ALL of them.
# 3. **NO REASONING:** Once you have the source code, do not explain. Just generate the full Pytest code.
# 4. **NO PARAMETRIZE:** Every test case MUST be a standalone `def test_...` function.

# ### ⛔ THE ABSOLUTE MOCKING RULE (NON-NEGOTIABLE):
# You are FORBIDDEN from using `mocker.patch('requests.get')`. 
# You MUST use this EXACT string for every requests mock:
# `mocker.patch('{import_path}.requests.get')`

# ### ⛔ CRITICAL IMPLEMENTATION DETAILS:
# - **IMPORTS:** Include `import pytest`, `import requests`, `import json`, and the correct import for the function under test.
# - **ADVANCED MOCKING:** If the code calls `response.raise_for_status()`, you MUST mock the `side_effect` of the `raise_for_status` method to raise `requests.exceptions.HTTPError`.
# - **TC ID:** Name each function using the TC ID from the plan (e.g., `test_tc001_...`).
# - **SAVE:** IMMEDIATELY call `write_local_file` with the complete code to: `{test_file_path}`.

# ### APPROVED TEST PLAN (THE SOURCE OF TRUTH):
# {plan}

# ### FINAL INSTRUCTION:
# Implement EXACTLY {tc_count} functions now. Use the EXACT patch path `{import_path}.requests.get`. 
# If you skip any TC ID from the plan above, you fail the task.
# """



# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Engineer.
# Your goal is to transform a Test Plan into actual, executable Pytest code.

# ### CONTEXT:
# - Target File: {target_file}
# - Import Path: {import_path} 
# - Destination Path: {test_file_path}
# - Test Framework: pytest
# - Mocking Tool: {mock_tool} (mocker fixture)

# ### REQUIRED STEPS:
# 1. **READ:** You MUST use `read_local_file` to read `{target_file}` before writing any code.
# 2. **IDENTIFY:** There are EXACTLY {tc_count} test cases in the plan below.
# 3. **IMPLEMENT:** Write EXACTLY {tc_count} separate, standalone functions.
# 4. **NO PARAMETRIZE:** Do NOT use `pytest.mark.parametrize`. Every test case MUST have its own `def test_...` function.

# ### APPROVED TEST PLAN:
# {plan}

# ### ⛔ THE ABSOLUTE MOCKING RULE (NON-NEGOTIABLE):
# You are FORBIDDEN from using `mocker.patch('requests.get')`. 
# If you use it, the test will NOT work because it patches the wrong namespace.

# Instead, you MUST use this EXACT line for every requests mock:
# `mock_get = mocker.patch('{import_path}.requests.get')`

# I will check this. Any deviation from this exact string `{import_path}.requests.get` is a failure.

# ### ⛔ CRITICAL REQUIREMENTS (MANDATORY):
# - **MANDATORY MOCKING:** You are FORBIDDEN from making real network calls. You MUST use the `mocker` fixture to patch `requests.get`.
# - **ADVANCED MOCKING:** If the source code calls `response.raise_for_status()`, you MUST define a `side_effect` for the `raise_for_status` method on the mock object to raise `requests.exceptions.HTTPError` for non-200 status codes. Do NOT just mock the `status_code`.
# - **IMPORTS:** You MUST include all necessary imports at the top (e.g., `import pytest`, `import requests`, `from scraper_service.scraper_api import fetch_studies`).
# - **TC ALIGNMENT:** Implement EXACTLY {tc_count} functions. Name them using the TC ID (e.g., `test_success_flow_TC01`).
# - **ISOLATION:** Each test function must contain its own dedicated mock setup.
# - **SAVE:** Use the `write_local_file` tool to save the complete code to {test_file_path}.

# ### EXAMPLE OF CORRECT PATCHING:
# If target_file is 'app/api.py' and it uses requests:
# CORRECT: `mocker.patch('app.api.requests.get')`
# INCORRECT: `mocker.patch('requests.get')`

# ### FINAL INSTRUCTION:
# I identified {tc_count} scenarios. Stop reasoning and implement ALL {tc_count} functions now using the EXACT patch path `{import_path}.requests.get`. 
# If you skip any TC or forget Mocks, the task is a failure.
# """

# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Engineer.
# Your goal is to transform a Test Plan into actual, executable code.

# ### CONTEXT:
# - Target File: {target_file}
# - Destination: {test_file_path}

# ### REQUIRED STEPS:
# 1. **READ:** Read `{target_file}` first.
# 2. **IDENTIFY:** There are EXACTLY {tc_count} test cases in the plan below.
# 3. **IMPLEMENT:** Write EXACTLY {tc_count} separate, standalone functions.
# 4. **NO PARAMETRIZE:** Do NOT use parametrize. Every test case gets its own `def test_...`.

# ### APPROVED TEST PLAN:
# {plan}

# ### CRITICAL REQUIREMENTS:
# - **NAMING:** Use the ID or number from the plan (e.g., `test_case_1_success`).
# - **MOCKING:** Use {mock_tool} inside each function.
# - **COMPLETENESS:** If you write fewer than {tc_count} functions, the task will fail.
# - **NO PARAMETRIZE:** Do NOT use `pytest.mark.parametrize`. You must write a standalone, unique function for EACH test case. 
# - **FUNCTIONAL MAPPING:** Every bullet point in the 'Logic Per Case' section MUST have a corresponding Python function.
# - **ISOLATION:** Each test function must contain its own setup and mocks. Do not share mock logic between functions to ensure clarity.

# ### FINAL INSTRUCTION:
# Implement ALL {tc_count} scenarios now.
# """


# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Engineer.
# Your goal is to transform a Test Plan into actual, executable code.

# ### CONTEXT:
# - Repo Root: {repo_path}
# - Source File to Test: {target_file}
# - Destination Path for Test: {test_file_path}

# ### SOURCE CODE FOR CONTEXT:
# {source_code}

# ### APPROVED TEST PLAN:
# {plan}

# ### TASK:
# 1. **IMPLEMENT** the Test Plan using {framework}.
# 2. **IMPORT:** Use statements relative to the Repo Root. 
#    Example: from {import_path} import ...
# 3. **SAVE:** Use the `write_local_file` tool to save the code directly to {test_file_path}.
# 4. **MOCKING:** Use {mock_tool} for all external calls.

# ### FINAL INSTRUCTION:
# Only output the Python code inside ```python blocks.
# """


# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Engineer.
# Your goal is to transform a Test Plan into actual, executable code.

# ### CONTEXT:
# - Repo Root: {repo_path}
# - Source File to Test: {target_file}
# - Destination Path for Test: {test_file_path}

# ### REQUIRED STEPS:
# 1. **READ:** You MUST use the `read_local_file` tool to read the contents of `{target_file}` first. You need this to understand the function signatures and logic.
# 2. **IMPLEMENT:** After reading, implement the approved Test Plan using {framework}.
# 3. **IMPORT:** Use statements relative to the Repo Root. 
#    Example: from {import_path} import ...
# 4. **SAVE:** Use the `write_local_file` tool to save the code to {test_file_path}.

# ### APPROVED TEST PLAN:
# {plan}

# ### FINAL INSTRUCTION:
# Ensure all mocks are correctly implemented using {mock_tool}.
# """

# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Engineer.
# Your goal is to transform a Test Plan into actual, executable code with 100% coverage.

# ### CONTEXT:
# - Repo Root: {repo_path}
# - Source File to Test: {target_file}
# - Destination Path for Test: {test_file_path}

# ### REQUIRED STEPS:
# 1. **READ:** You MUST use the `read_local_file` tool to read `{target_file}`.
# 2. **PLAN REVIEW:** Identify EVERY test case ID (e.g., TC01, TC02) in the plan below.
# 3. **IMPLEMENT:** Write EXACTLY one `pytest` function for each identified test case.
# 4. **IMPORT:** Use statements relative to the Repo Root: `from {import_path} import ...`
# 5. **SAVE:** Use the `write_local_file` tool to save to {test_file_path}.

# ### APPROVED TEST PLAN:
# {plan}

# ### CRITICAL REQUIREMENTS:
# - **NO OMMISSIONS:** Do not skip any test cases from the plan. If the plan has 6 cases, you must write 6 functions.
# - **MOCKING:** Use {mock_tool} for all external dependencies.
# - **NAMING (REQUIRED):** You MUST include the TC ID in every function name (e.g., test_description_TC01). This is how I verify your coverage.

# ### FINAL INSTRUCTION:
# Start by reading the source file. Then, implement the FULL plan. 
# Do not stop until every TC is covered.
# """




# WRITER_PROMPT_TEMPLATE = """
# ### ROLE:
# You are a Senior Backend Developer and QA Automation Engineer.
# Your goal is to transform a Test Plan into actual, executable code.

# ### CONTEXT:
# - Repo Root: {repo_path}
# - Source File to Test: {target_file}
# - Destination Path for Test: {test_file_path}

# ### REQUIRED STEPS:
# 1. **READ:** You MUST use the `read_local_file` tool to read the contents of `{target_file}` first.
# 2. **IMPLEMENT:** After reading, implement the approved Test Plan using {framework}.
# 3. **IMPORT:** Use statements like: `from {import_path} import ...`
# 4. **SAVE:** Use the `write_local_file` tool to save the code to {test_file_path}.

# ### APPROVED TEST PLAN (MUST IMPLEMENT ALL):
# {plan}

# ### CRITICAL REQUIREMENTS:
# - Framework: {framework}
# - Mocking: Use {mock_tool} for all external API calls and side effects.
# - DO NOT return a generic 'assert True' test.
# - Implement the full logic for EVERY test case listed in the plan above.
# - You MUST use the `write_local_file` tool to provide the final code.
# """