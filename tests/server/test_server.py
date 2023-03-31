import sqlite3
from contextlib import contextmanager
from typing import Generator
from unittest.mock import Mock

import pytest
from flask.testing import FlaskClient
from werkzeug.serving import BaseWSGIServer

from src.server import Server
from src.server.database import DatabaseHandler, DatabaseProvider, Message


class Test_Server:
    @pytest.fixture(name="server")
    def mock_server(self) -> Server:
        server = Server()
        server.server = Mock(BaseWSGIServer)
        server.app.config.update({"TESTING": True})

        return server

    @pytest.fixture(name="client")
    def mock_client(self, server: Server) -> FlaskClient:
        return server.app.test_client()

    @pytest.fixture(name="cursor")
    def mock_cursor(self) -> Mock:
        mock = Mock(sqlite3.Cursor)
        return mock

    @pytest.fixture(name="failing_database_handler")
    def mock_database_handler(
        self, monkeypatch: pytest.MonkeyPatch, cursor: sqlite3.Cursor
    ) -> Mock:
        @contextmanager
        def mocked_handler() -> Generator[DatabaseHandler, None, None]:
            yield DatabaseHandler(cursor, Message.UNKNOWN_ERROR)

        mock = Mock(side_effect=mocked_handler)
        monkeypatch.setattr(DatabaseProvider, "handler", mock)
        return mock

    class Test_Auth:
        class Test_RegisterEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.url_path: str = "api/v1/auth/register"
                self.client: FlaskClient = client

            def test_send_400_on_invalid_json_format(self, client: FlaskClient) -> None:
                response = client.post(
                    self.url_path,
                    data={
                        "email": "legit_email@gmail.com",
                        "totally_wrong_key": "what_even_is_this",
                    },
                )
                assert response.status_code == 400

            def test_send_500_on_internal_error(self, failing_database_handler: Mock) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                assert response.status_code == 500

            def test_send_202_when_user_exists(self) -> None:
                self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                response = self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                assert response.status_code == 202

            def test_send_201_on_success(self) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                assert response.status_code == 201

        class Test_LoginEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.register_path: str = "api/v1/auth/register"
                self.url_path: str = "api/v1/auth/login"
                self.client: FlaskClient = client

            def test_send_400_on_invalid_json_format(self, client: FlaskClient) -> None:
                response = client.post(
                    self.url_path,
                    data={
                        "email": "legit_email@gmail.com",
                        "totally_wrong_key": "what_even_is_this",
                    },
                )
                assert response.status_code == 400

            def test_send_500_on_internal_error(self, failing_database_handler: Mock) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                assert response.status_code == 500

            def test_send_401_when_unauthorized(self) -> None:
                # basically we are trying to login without registering
                response = self.client.post(
                    self.url_path,
                    json={"email": "not_legit_email@gmail.com", "password": "nice_try"},
                )
                assert response.status_code == 401

            def test_send_201_on_success(self) -> None:
                # register and then login
                self.client.post(
                    self.register_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )

                response = self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                assert response.status_code == 201

            def test_send_403_when_cannot_verify(self) -> None:
                # register and then try to login with wrong password
                self.client.post(
                    self.register_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )

                response = self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "wrong_password"},
                )
                assert response.status_code == 403
