"""python -m evaluation retrieval | rag"""

from dotenv import load_dotenv

load_dotenv()

from shared.logging_config import configure_logging

configure_logging()

from evaluation.runner import main

raise SystemExit(main())
