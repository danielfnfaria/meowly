"""`GET /v1/info`: what the UI shows in its footer."""

from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter

from purr_api.schemas.info import InfoOut
from purr_contracts import SPEC_VERSION

router = APIRouter(tags=["info"])

PRODUCT = "purr"


def _api_version() -> str:
    try:
        return version("purr-api")
    except PackageNotFoundError:  # running from a checkout that was never installed
        return "0.0.0"


@router.get("/info", operation_id="get_info")
async def get_info() -> InfoOut:
    return InfoOut(product=PRODUCT, api_version=_api_version(), spec_version=SPEC_VERSION)
