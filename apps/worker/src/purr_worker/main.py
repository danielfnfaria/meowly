import sys

from purr_worker.pod import run_task
from purr_worker.settings import get_settings


def run() -> None:
    """`purr-worker`: run the task the Job was created for and exit with its outcome."""
    sys.exit(run_task(get_settings()))


if __name__ == "__main__":
    run()
