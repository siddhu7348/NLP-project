"""Command-line usage:
    python main.py --resume data/sample_resume.txt --jd data/sample_job_description.txt
"""
import argparse
import json
from pathlib import Path

from src.config import load_config
from src.parser import text_from_file
from src.screener import screen_resume


def main():
    parser = argparse.ArgumentParser(description="LLM-powered resume screener")
    parser.add_argument("--resume", required=True, help="Path to resume (.pdf or .txt)")
    parser.add_argument("--jd", required=True, help="Path to job description (.txt)")
    parser.add_argument("--json", action="store_true", help="Print raw JSON")
    args = parser.parse_args()

    cfg = load_config()
    result = screen_resume(
        text_from_file(args.resume), Path(args.jd).read_text(encoding="utf-8"), cfg
    )

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"\nMatch score : {result['match_score']}/100  ->  {result['decision']}")
    print(f"Summary     : {result['summary']}\n")
    for title, key in [
        ("Matched skills", "matched_skills"),
        ("Missing skills", "missing_skills"),
        ("Strengths", "strengths"),
        ("Concerns", "concerns"),
        ("Suggestions", "suggestions"),
    ]:
        print(f"{title}:")
        for item in result[key]:
            print(f"  - {item}")
        print()


if __name__ == "__main__":
    main()
