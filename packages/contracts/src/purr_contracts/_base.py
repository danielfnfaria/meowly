from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    """Base of every wire model: an unknown field is an error, never silently dropped.

    Not frozen: the controller and the worker build a new status from the previous one, and
    pydantic's `model_copy(update=...)` is enough of a guard against accidental mutation.
    """

    model_config = ConfigDict(extra="forbid")
