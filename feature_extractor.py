
import argparse
import os

from dotenv import load_dotenv

from ml_predictor.utils import scan_repo_to_excel
from shared.repo_cli import add_repo_path_argument, resolve_repo_path


if __name__ == "__main__":
    load_dotenv()
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

    print(f"--- מתחיל סריקה של התיקייה: {os.path.abspath(path_to_my_repo)} ---")
    df_results = scan_repo_to_excel(path_to_my_repo, output_excel_name)

    if df_results is not None:
        print("\n--- סריקה הושלמה בהצלחה! ---")
        print(f"נוצר קובץ אקסל בשם: {output_excel_name}")
        print("\n5 השורות הראשונות מהסריקה:")
        print(df_results.head())
    else:
        print("\n--- הסריקה הסתיימה ללא תוצאות ---")
