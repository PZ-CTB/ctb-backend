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

    @classmethod
    def initialize(cls) -> None:
        """Load schema files."""
        with open("res/schemas/login.json", encoding="utf-8") as f:
            cls.login_schema = json.load(f)
        with open("res/schemas/register.json", encoding="utf-8") as f:
            cls.register_schema = json.load(f)

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
                except ValidationError:
                    return Responses.invalid_json_format_error()
                return fun(*args, **kwargs)

            return decorated

        return decorator
