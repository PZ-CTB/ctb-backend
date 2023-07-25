import json
import logging
from functools import wraps
from pathlib import Path
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
        logging.info("Loading schemas...")
        files = [p.stem for p in Path(PATHS.VALIDATION_SCHEMAS).iterdir() if p.is_file()]
        for schema in files:
            with open(f"{PATHS.VALIDATION_SCHEMAS}{schema}.json") as file:
                cls.schemas[schema] = json.load(file)
        logging.info("Schemas loaded.")

    @classmethod
    def get_schema(cls, schema: str) -> dict:
        """Get schema by name."""
        return cls.schemas.get(schema, {})

    @classmethod
    def validate(
        cls, schema_name: str
    ) -> Callable[[Callable[..., Response]], Callable[..., Response]]:  # xD
        """Validate received JSON against given schema."""

        def decorator(fun: Callable[..., Response]) -> Callable[..., Response]:
            @wraps(fun)
            def decorated(*args: tuple, **kwargs: dict) -> Response:
                try:
                    validate(request.get_json(), SchemaValidator.get_schema(schema_name))
                except ValidationError as e:
                    logging.error(f"{e=}")
                    return Responses.invalid_json_format_error()
                return fun(*args, **kwargs)

            return decorated

        return decorator
