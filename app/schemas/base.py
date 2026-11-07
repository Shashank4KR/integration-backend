from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema for all incoming request payloads.

    - extra='forbid': Strictly disallows unexpected or extraneous fields,
      preventing mass-assignment vulnerabilities.
    - str_strip_whitespace=True: Trims leading/trailing whitespace on all string fields.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class StrictBaseSchema(BaseModel):
    """Strict base schema for models with scalar-only fields where strict=True is safe.

    Rejects implicit type coercions (e.g., "123" -> 123 or 123.4 -> 123).
    Note: strict=True should NOT be used on schemas that accept JSON date/datetime/UUID strings,
    as Pydantic strict mode requires native Python date/datetime/UUID instances.
    """

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class ResponseSchema(BaseModel):
    """Base schema for outbound responses reading from ORM instances."""

    model_config = ConfigDict(
        from_attributes=True,
    )
