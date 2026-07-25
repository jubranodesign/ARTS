from dotenv import load_dotenv

from evaluation.retrieval.eval_utils import run_retrieval_suite
from services.vector_db_service import VectorDBService
from shared.logging_config import configure_logging

load_dotenv()
configure_logging()

run_retrieval_suite(vdb=VectorDBService())
