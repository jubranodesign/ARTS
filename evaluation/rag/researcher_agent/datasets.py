sample = {
    "question": "Analyze fetch_studies: API URL, query params, timeout, and error handling.",
    "contexts": [
        'API_URL = "https://clinicaltrials.gov/api/v2/studies"',
        'params = {"pageSize": page_size, "format": "json"}',
        "response = requests.get(API_URL, params=params, timeout=10)",
        "response.raise_for_status()",
        'return response.json().get("studies", [])',
        "except requests.exceptions.Timeout:",
        "except requests.exceptions.HTTPError as http_err:",
        "status_code = http_err.response.status_code",
    ],
    "answer": """
    ### RESEARCH_DATA_DUMP ###
    - FUNCTION: fetch_studies(page_size)
    - API: GET clinicaltrials.gov/api/v2/studies with pageSize and format=json, timeout=10s.
    - SUCCESS: raise_for_status(), return studies list from JSON .get("studies", []).
    - VALIDATION: ValueError if page_size is not a positive integer.
    - ERRORS: Timeout, HTTPError (logs status), RequestException — all log and return [].
    """,
    "ground_truth": (
        "fetch_studies validates positive page_size, GETs the Clinical Trials API v2 URL "
        "with pageSize and format=json and a 10 second timeout, returns the studies list "
        "from JSON on success, and on Timeout, HTTPError, or RequestException logs the error "
        "and returns an empty list."
    ),
}
