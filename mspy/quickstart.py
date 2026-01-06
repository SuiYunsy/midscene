"""
快速体验脚本：
uv run python quickstart.py --url https://example.org --instruction "describe the page"
"""

from __future__ import annotations

import argparse
import json

from mspy.core.service import MidsceneService
from mspy.shared.env import load_env
from mspy.shared.logger import get_logger

logger = get_logger("mspy.quickstart")


def main():
    parser = argparse.ArgumentParser(description="Run Midscene Python quickstart")
    parser.add_argument("--url", required=True, help="Target page url")
    parser.add_argument(
        "--instruction",
        required=True,
        help="User instruction, e.g. 'login and click submit'",
    )
    args = parser.parse_args()

    env = load_env()
    service = MidsceneService(env)
    plans = service.plan_and_run(args.url, args.instruction, max_steps=2)
    logger.info("Plan result:\n%s", json.dumps(plans, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
