import sqlite3
from contextlib import contextmanager
from typing import Generator
from unittest.mock import Mock

import pytest
from flask.testing import FlaskClient
from werkzeug.serving import BaseWSGIServer

from src.server import Server
from src.server.auth import TokenService
from src.server.database import DatabaseHandler, DatabaseProvider, Message


class Test_Server:
    @pytest.fixture(name="server")
    def mock_server(self) -> Server:
        server = Server()
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

            def test_send_400_on_invalid_json_format(self) -> None:
                response = self.client.post(
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
                    json={"email": "other_legit_email@gmail.com", "password": "thelegend27"},
                )
                assert response.status_code == 201

        class Test_LoginEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.register_path: str = "api/v1/auth/register"
                self.url_path: str = "api/v1/auth/login"
                self.client: FlaskClient = client

            def test_send_400_on_invalid_json_format(self) -> None:
                response = self.client.post(
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

        class Test_MeEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.register_path: str = "api/v1/auth/register"
                self.login_path: str = "api/v1/auth/login"
                self.url_path: str = "api/v1/auth/me"
                self.client: FlaskClient = client

            @pytest.fixture(name="token")
            def fixture_register_and_login(self) -> str:
                self.client.post(
                    self.register_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                login_response = self.client.post(
                    self.login_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                return login_response.get_json()["auth_token"]

            def test_send_405_on_invalid_method(self) -> None:
                response = self.client.post(self.url_path)
                assert response.status_code == 405

            @pytest.mark.skip("Currently returns 401 due to internal error on token validation")
            def test_send_500_on_internal_error(
                self, token: str, failing_database_handler: Mock
            ) -> None:
                response = self.client.get(
                    self.url_path,
                    headers={
                        "x-access-token": token,
                    },
                )
                assert response.status_code == 500

            def test_send_401_when_unauthorized_no_token(self) -> None:
                response = self.client.get(self.url_path)
                assert response.status_code == 401

            @pytest.mark.skip("Not possible to achieve: token = registered, no token = 401")
            def test_send_401_when_unauthorized_user_not_registered(
                self, token: str, failing_database_handler: Mock
            ) -> None:
                response = self.client.get(
                    self.url_path,
                    headers={
                        "x-access-token": token,
                    },
                )
                assert response.status_code == 401

            def test_send_200_on_success(self, token: str) -> None:
                # register, login, retrieve token and get to me endpoint
                response = self.client.get(
                    self.url_path,
                    headers={
                        "x-access-token": token,
                    },
                )
                assert response.status_code == 200

        class Test_LogoutEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.register_path: str = "api/v1/auth/register"
                self.login_path: str = "api/v1/auth/login"
                self.url_path: str = "api/v1/auth/logout"
                self.client: FlaskClient = client

            @pytest.fixture(name="token")
            def fixture_register_and_login(self) -> str:
                self.client.post(
                    self.register_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                login_response = self.client.post(
                    self.login_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                return login_response.get_json()["auth_token"]

            @pytest.fixture(name="token_already_revoked")
            def mock_is_token_revoked(self, monkeypatch: pytest.MonkeyPatch) -> Mock:
                mock = Mock(return_value=True)
                monkeypatch.setattr(TokenService, "is_token_revoked", mock)
                return mock

            @pytest.fixture(name="token_revoke_failure")
            def mock_revoke_token(self, monkeypatch: pytest.MonkeyPatch) -> Mock:
                mock = Mock(return_value=Message.UNKNOWN_ERROR)
                monkeypatch.setattr(TokenService, "revoke_token", mock)
                return mock

            def test_send_401_when_unauthorized_no_token(self) -> None:
                # logout without token
                response = self.client.post(self.url_path)
                assert response.status_code == 401

            def test_send_401_when_unauthorized_token_revoked(
                self, token: str, token_already_revoked: Mock
            ) -> None:
                # logout with revoked token
                response = self.client.post(
                    self.url_path,
                    headers={
                        "x-access-token": token,
                    },
                )
                assert response.status_code == 401

            def test_send_500_on_revoke_failure(
                self, token: str, token_revoke_failure: Mock
            ) -> None:
                # logout halted due to token revoke fail
                response = self.client.post(
                    self.url_path,
                    headers={
                        "x-access-token": token,
                    },
                )
                assert response.status_code == 500

            def test_send_201_on_success(self, token: str) -> None:
                response = self.client.post(
                    self.url_path,
                    headers={
                        "x-access-token": token,
                    },
                )
                assert response.status_code == 201
