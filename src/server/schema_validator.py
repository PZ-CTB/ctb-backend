import json
from functools import wraps
from typing import Callable

from flask import Response, request
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from . import PATHS, Responses


class SchemaValidator:
    """Class for validating JSON requests."""

    schemas: dict = {}

    @classmethod
    def initialize(cls) -> None:
        """Load schema files."""
        print("INFO: server.schema_validator.SchemaValidator.initialize(): Loading schemas...")
        for schema in ["register", "login", "deposit"]:
            with open(f"{PATHS.VALIDATION_SCHEMAS}{schema}.json") as file:
                cls.schemas[schema] = json.load(file)
        print("INFO: server.schema_validator.SchemaValidator.initialize(): Schemas loaded.")

    @classmethod
    def get_schema(cls, schema: str) -> dict:
        """Get schema by name."""
        return cls.schemas.get(schema, {})

    @classmethod
    def validate(
        cls, schema: dict
    ) -> Callable[[Callable[..., Response]], Callable[..., Response]]:  # xD
        """Validate received JSON against given schema."""

        def decorator(fun: Callable[..., Response]) -> Callable[..., Response]:
            @wraps(fun)
            def decorated(*args: tuple, **kwargs: dict) -> Response:
                try:
                    validate(request.get_json(), schema)
                except ValidationError as e:
                    print(f"ERROR: server.schema_validator.SchemaValidator.validate(): {e}")
                    return Responses.invalid_json_format_error()
                return fun(*args, **kwargs)

            return decorated

        return decorator
