import kopf

from purr_controller.handlers import register
from purr_controller.settings import get_settings
from purr_runtime import configure_logging

# Held at WARNING: per-object kopf chatter.
QUIET_LOGGERS = ("httpx", "httpcore", "kopf.objects")


def run() -> None:
    """`purr-controller`: run the kopf operator in the execution namespace until SIGTERM."""
    cfg = get_settings()
    configure_logging(cfg.log_level, quiet=QUIET_LOGGERS)
    register()
    kopf.run(
        standalone=True,  # no peering CRDs: one replica owns the namespace
        clusterwide=False,  # a Role, not a ClusterRole
        namespaces=[cfg.execution_namespace],
    )


if __name__ == "__main__":
    run()
