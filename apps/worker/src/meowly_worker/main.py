import sys

from meowly_worker.pod import run_task
from meowly_worker.settings import get_settings


def run() -> None:
    """`meowly-worker`: run the task the Job was created for and exit with its outcome."""
    sys.exit(run_task(get_settings()))


if __name__ == "__main__":
    run()
