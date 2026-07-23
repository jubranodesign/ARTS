from evaluation.retrieval.eval_utils import run_retrieval_suite
from services.vector_db_service import VectorDBService

run_retrieval_suite(vdb=VectorDBService())
