# Ground-truth keywords are matched against Chroma page_content (LLM summaries), not
# metadata["source_code"] or BM25. See README § Offline evaluation / Ingestion & retrieval storage.

# TEST_SET for fetch_studies (clinicaltrials.gov API v2 client)
test_set = [
    ("where is the clinical trials API base URL defined", "clinicaltrials.gov/api/v2/studies"),
    ("how are pageSize and format query parameters built for the API", "pageSize"),
    ("how does the code call GET with timeout", "timeout=10"),
    ("what happens when the HTTP response status is an error", "raise_for_status"),
    ("how are studies extracted from the JSON response body", '.get("studies"'),
    ("validation when page_size is not a positive integer", "page_size must be a positive integer"),
    ("handling API request timeout errors", "requests.exceptions.Timeout"),
    ("logging HTTP errors with status code", "HTTPError"),
    ("network or request failures besides timeout and HTTP", "RequestException"),
    ("module logger used for error messages", "logging.getLogger"),
]
