from meowly_api.schemas.base import Out


class InfoOut(Out):
    """What the UI shows in its footer."""

    product: str
    api_version: str
    spec_version: int
