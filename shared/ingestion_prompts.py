CHUNK_SUMMARY_PROMPT = """
You are an expert code analyst inside an advanced AI-Agent RAG system.
Your job is to analyze the following Python code chunk and generate a concise, high-quality semantic description of what this code achieves from a functional and business logic perspective.

CRITICAL RULES:
1. Focus ONLY on the "What" and "Why" (e.g., "Calculates user ROI and updates the database context", "Validates JWT access tokens for incoming requests").
2. DO NOT describe the syntax or code structure (DO NOT say: "This chunk contains a for loop", "This is a class method", "This imports os").
3. Keep it brief: 1-2 sentences maximum.
4. Respond ONLY with the description. No greetings, no markdown formatting, no code blocks.

Code Chunk to analyze:
{code_content}

Description:
"""

SEED_SUMMARY_PROMPT = """
You are an expert QA Automation and Test Infrastructure analyst inside an advanced AI-Agent RAG system.
Your job is to analyze the following Pytest/Python test code (SEED DATA) and generate a high-quality structural and architectural summary. 
This summary will be used to match this seed with target source code files that share similar code patterns.

CRITICAL RULES:
1. FOCUS ON TECHNIQUES & PATTERNS: Describe exactly WHAT coding patterns this test handles (e.g., "Context Managers with blocks", "Third-party HTTP exceptions", "Internal module namespace mocking") and HOW it handles them.
2. EXTRACT STRUCTURAL ANCHORS: Mention direct code structures being verified or mocked (e.g., "mocker.patch absolute paths", "return_value.__enter__ chaining", "caplog text assertions").
3. BUSINESS IS SECONDARY: Keep the functional context minimal (e.g., "for database operations"). The mocking architecture is what matters.
4. Keep it brief: 2-3 sentences maximum.
5. Respond ONLY with the description. No greetings, no markdown formatting, no code blocks.

Test Code Chunk to analyze:
{code_content}

Description:
"""