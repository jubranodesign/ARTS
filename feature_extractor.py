
import argparse
import logging
import os

from dotenv import load_dotenv

from ml_predictor.utils import scan_repo_to_excel
from shared.logging_config import configure_logging
from shared.repo_cli import add_repo_path_argument, resolve_repo_path

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    load_dotenv()
    configure_logging()
    parser = argparse.ArgumentParser(description="Scan a repository and export ML metrics to CSV.")
    add_repo_path_argument(parser)
    parser.add_argument(
        "-o",
        "--output",
        default="my_repo_metrics.csv",
        help="Output CSV filename (default: my_repo_metrics.csv).",
    )
    args = parser.parse_args()
    path_to_my_repo = resolve_repo_path(args.repo_path)

    output_excel_name = args.output

    logger.info("Starting scan of directory: %s", os.path.abspath(path_to_my_repo))
    df_results = scan_repo_to_excel(path_to_my_repo, output_excel_name)

    if df_results is not None:
        logger.info("Scan completed successfully; output file: %s", output_excel_name)
        logger.debug("First 5 rows:\n%s", df_results.head())
    else:
        logger.warning("Scan finished with no results")
