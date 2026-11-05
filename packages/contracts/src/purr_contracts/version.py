from typing import Final

SPEC_VERSION: Final = 1
"""Version of the task wire (`TaskSpec`, `TaskStatus`, `TaskEvent`).

Bump it on any change to those models and keep the worker reading the previous version for at
least one release: a PlatformTask created before an upgrade is still executed after it.
"""
