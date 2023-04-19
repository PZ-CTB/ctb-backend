import json
from functools import wraps
from typing import Callable

from flask import Response, request
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from . import Responses


class SchemaValidator:
    """Class for validating JSON requests."""

    login_schema: dict = {}
    register_schema: dict = {}
    deposit_schema: dict = {}

    @classmethod
    def initialize(cls) -> None:
        """Load schema files."""
        print("INFO: server.schema_validator.SchemaValidator.initialize(): Loading schemas...")
        for schema in ("login", "register", "deposit"):
            with open(f"res/schemas/{schema}.json", encoding="utf-8") as f:
                cls.__dict__[f"{schema}_schema"] = json.load(f)
        print("INFO: server.schema_validator.SchemaValidator.initialize(): Schemas loaded.")

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
