import argparse
import logging
import os
import pickle
from enum import Enum

from dotenv import load_dotenv
from langchain_community.retrievers import BM25Retriever

from services.code_processor import CodeProcessor
from services.document_factory import DocumentFactory
from services.scanner import CodeScanner
from services.vector_db_service import VectorDBService
from shared.paths import DATA_DIR, VECTOR_STORE_PATH, get_repo_path, get_repo_seed_path
from shared.ingestion_prompts import CHUNK_SUMMARY_PROMPT, SEED_SUMMARY_PROMPT
from utils.retrieval import (
    prepare_bm25_documents,
    print_chunks_summary,
    python_code_tokenizer,
)

logger = logging.getLogger(__name__)


class IngestMode(str, Enum):
    SEED = "seed"
    SOURCE = "source"


def resolve_ingest_target(repo_root: str, mode: IngestMode) -> tuple[str, bool]:
    if mode == IngestMode.SEED:
        return get_repo_seed_path(repo_root), True
    return repo_root, False


def default_prompt_for_mode(mode: IngestMode) -> str:
    return SEED_SUMMARY_PROMPT if mode == IngestMode.SEED else CHUNK_SUMMARY_PROMPT


def run_ingestion(
    vdb: VectorDBService,
    provider="mistral",
    prompt=CHUNK_SUMMARY_PROMPT,
    is_test=False,
    repo_path: str | None = None,
    processor=None,
):
    logger.info("Ingestion script started")
    resolved_repo = repo_path or get_repo_path()
    logger.info(
        "Starting ingestion for: %s (Mode: %s)",
        resolved_repo,
        "Test/Seed" if is_test else "Source Code",
    )

    scanner = CodeScanner()
    factory = DocumentFactory()
    proc = processor or CodeProcessor(provider=provider, summary_prompt=prompt)

    try:
        file_paths, root_path = scanner.scan(resolved_repo)
        documents = [
            doc
            for p in file_paths
            if (doc := factory.create_document(p, root_path, is_test=is_test)) is not None
        ]

        chunks = proc.process(documents)
        print_chunks_summary(chunks)

        success = vdb.save_documents(chunks)

        dependency_retriever = None
        if not is_test:
            logger.info("Building BM25 keyword index for source code...")
            bm25_documents = prepare_bm25_documents(chunks)

            dependency_retriever = BM25Retriever.from_documents(
                bm25_documents,
                preprocess_func=python_code_tokenizer,
            )

            bm25_index_path = os.path.join(DATA_DIR, "bm25_index.pkl")
            with open(bm25_index_path, "wb") as f:
                pickle.dump(dependency_retriever, f)
            logger.info("BM25 index saved to: %s", bm25_index_path)
        else:
            logger.info("Skipping BM25 indexing (not required for Seed/Test data)")

        is_successful = success and (is_test or dependency_retriever is not None)

        if is_successful:
            logger.info(
                "Ingestion completed successfully; data persisted in: %s",
                VECTOR_STORE_PATH,
            )
        else:
            logger.error("Ingestion failed during database saving")

    except Exception as e:
        logger.error("Unexpected error during ingestion: %s", e)


def run_ingestion_for_repo(
    vdb: VectorDBService,
    mode: IngestMode = IngestMode.SEED,
    repo_root: str | None = None,
    provider: str = "mistral",
    processor: CodeProcessor | None = None,
) -> None:
    """Run ingestion for seed_data or full source tree under repo_root."""
    root = repo_root or get_repo_path()
    ingest_path, is_test = resolve_ingest_target(root, mode)
    prompt = default_prompt_for_mode(mode)
    proc = processor or CodeProcessor(provider=provider, summary_prompt=prompt)
    run_ingestion(
        vdb=vdb,
        provider=provider,
        prompt=prompt,
        is_test=is_test,
        repo_path=ingest_path,
        processor=proc,
    )


def run_both_ingestion(
    vdb: VectorDBService,
    repo_root: str | None = None,
    provider: str = "mistral",
) -> None:
    """Seed/golden tests first, then full source (Chroma + BM25)."""
    run_ingestion_for_repo(vdb, IngestMode.SEED, repo_root=repo_root, provider=provider)
    run_ingestion_for_repo(vdb, IngestMode.SOURCE, repo_root=repo_root, provider=provider)


if __name__ == "__main__":
    from shared.logging_config import configure_logging
    from shared.repo_cli import add_repo_path_argument, resolve_repo_path

    load_dotenv()
    configure_logging()

    parser = argparse.ArgumentParser(description="Ingest repository code into the vector store.")
    add_repo_path_argument(parser)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--full",
        action="store_true",
        help="Ingest the full source repository only.",
    )
    mode_group.add_argument(
        "--both",
        action="store_true",
        help="Ingest seed data, then full source (recommended setup).",
    )
    args = parser.parse_args()
    repo_root = resolve_repo_path(args.repo_path)

    vdb = VectorDBService()
    if args.both:
        run_both_ingestion(vdb, repo_root=repo_root)
    elif args.full:
        run_ingestion_for_repo(vdb, IngestMode.SOURCE, repo_root=repo_root)
    else:
        run_ingestion_for_repo(vdb, IngestMode.SEED, repo_root=repo_root)
