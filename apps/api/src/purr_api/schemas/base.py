import uuid
from datetime import datetime
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator


class ErrorOut(BaseModel):
    """Every error this API returns: `purr_http.errors` maps a domain error to a status and
    this body. It is declared on the routes (not only implemented) because the UI client is
    generated from the OpenAPI (ADR 0004): an error shape the schema does not mention is an
    error the UI has to guess."""

    code: str
    message: str


class Body(BaseModel):
    """Base of every request body: an unknown field is a 422, not silently dropped."""

    model_config = ConfigDict(extra="forbid")


class Out(BaseModel):
    """Base of every response body; reads ORM objects directly."""

    model_config = ConfigDict(from_attributes=True)


class EntityOut(Out):
    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime


class Patch(Body):
    """Base of the update bodies: every field optional, only the ones sent are applied.

    Sending `null` is only accepted for the fields in `NULLABLE` (the column takes NULL);
    for the others it is a 422 here instead of an integrity error from the database.
    """

    NULLABLE: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _reject_null_for_required(self) -> Self:
        for name in self.model_fields_set:
            if getattr(self, name) is None and name not in self.NULLABLE:
                raise ValueError(f"{name} cannot be null")
        return self

    def sent(self) -> dict[str, object]:
        """Only the fields the client actually sent."""
        return {name: getattr(self, name) for name in self.model_fields_set}
