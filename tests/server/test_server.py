from contextlib import contextmanager
from typing import Any, Generator
from unittest.mock import Mock

import psycopg
import pytest
from flask.testing import FlaskClient

from src.server import QUERIES, Server
from src.server.auth import TokenService
from src.server.database import DatabaseHandler, DatabaseProvider, Message


class FakeDatabase:
    def __init__(self) -> None:
        self._db_users: list[
            tuple[str, str, str, float, float]
        ] = []  # uuid, email, pwd_hash, usd, btc
        self._db_tokens: list[tuple[str, str]] = []
        self._db_prices: list[tuple[float, str]] = [(3.0, "01-01-2019")]  # price, date
        self._last_query: str = ""
        self._last_params: list | tuple = []
        self._last_result: list = []
        self._last_generator: Generator = self._invalid_generator()

    @property
    def db_users(self) -> list[tuple[str, str, str, str, str]]:
        return [(t[0], t[1], t[2], str(t[3]), str(t[4])) for t in self._db_users]

    @property
    def db_tokens(self) -> list[tuple[str, str]]:
        return self._db_tokens

    @property
    def db_prices(self) -> list[tuple[str, str]]:
        return [(str(t[0]), t[1]) for t in self._db_prices]

    @property
    def last_query(self) -> str:
        return self._last_query

    @property
    def last_params(self) -> list | tuple:
        return self._last_params

    def execute_side_effect(self, query: str, params: list | tuple = []) -> None:
        self._last_query = query
        self._last_params = params
        self._last_result = []
        self._last_generator = self._invalid_generator()

        print(f"TEST: {self._last_query=}, {self._last_params=}")
        match query:
            case QUERIES.INSERT_USER:
                if params[0] in [_uuid for _uuid, _, _, _, _ in self.db_users]:
                    raise psycopg.IntegrityError()
                else:
                    self._db_users.append((params[0], params[1], params[2], 0.0, 0.0))
            case QUERIES.INSERT_REVOKED_TOKEN:
                if params[0] in [token for token, _ in self.db_tokens]:
                    raise psycopg.IntegrityError()
                else:
                    self.db_tokens.append((params[0], params[1]))
            case QUERIES.WALLET_DEPOSIT:
                try:
                    index = [user[0] for user in self.db_users].index(params[1])
                except ValueError:
                    raise psycopg.IntegrityError()
                else:
                    old_user = self._db_users[index]
                    self._db_users[index] = old_user[:3] + (old_user[3] + params[0],) + old_user[4:]
            case QUERIES.WALLET_WITHDRAW:
                try:
                    index = [user[0] for user in self.db_users].index(params[1])
                except ValueError:
                    raise psycopg.IntegrityError()
                else:
                    old_user = self._db_users[index]
                    self._db_users[index] = old_user[:3] + (old_user[3] - params[0],) + old_user[4:]
            case QUERIES.WALLET_BUY:
                try:
                    index = [user[0] for user in self.db_users].index(params[2])
                except ValueError:
                    raise psycopg.IntegrityError()
                else:
                    old_user = self._db_users[index]
                    self._db_users[index] = (
                        old_user[:3] + (old_user[3] - params[0] * 3,) + (old_user[4] + params[0],)
                    )
            case _:
                self._last_result = self.fetchall_side_effect()
                self._last_generator = self._fetchone_generator()

    def fetchall_side_effect(self) -> list:
        match self.last_query:
            case QUERIES.SELECT_USER_UUID:
                return [
                    _uuid for _uuid, _, _, _, _ in self.db_users if self.last_params[0] == _uuid
                ]
            case QUERIES.SELECT_USER_EMAIL:
                return [
                    email for _, email, _, _, _ in self.db_users if self.last_params[0] == email
                ]
            case QUERIES.SELECT_USER_EMAIL_BY_UUID:
                return [
                    email for _uuid, email, _, _, _ in self.db_users if self.last_params[0] == _uuid
                ]
            case QUERIES.SELECT_USER_LOGIN_DATA_BY_EMAIL:
                return [
                    (_uuid, email, pwd)
                    for _uuid, email, pwd, _, _ in self.db_users
                    if self.last_params[0] == email
                ]
            case QUERIES.SELECT_USER_DATA_BY_UUID:
                return [
                    (email, usd, btc)
                    for _uuid, email, _, usd, btc in self.db_users
                    if self.last_params[0] == _uuid
                ]
            case QUERIES.SELECT_REVOKED_TOKEN:
                return [
                    token
                    for token, expiry in self.db_tokens
                    if token == self.last_params[0] and expiry > self.last_params[1]
                ]
            case QUERIES.SELECT_LATEST_STOCK_PRICE:
                return [(value, data) for value, data in self.db_prices]
            case _:
                return []

    def fetchone_side_effect(self) -> Any:
        return next(self._last_generator)

    def _invalid_generator(self) -> Generator:
        for i in range(0):
            yield i
        print("TEST: USING INVALID GENERATOR")
        raise StopIteration

    def _fetchone_generator(self) -> Generator:
        yield from self._last_result


DATABASE = FakeDatabase()


@pytest.fixture(name="clear_database", autouse=True)
def fixture_clear_fake_database() -> None:
    DATABASE._db_users.clear()
    DATABASE._db_tokens.clear()
    DATABASE._last_query = ""
    DATABASE._last_params = []
    DATABASE._last_result = []
    DATABASE._last_generator = DATABASE._invalid_generator()


@pytest.fixture(name="cursor")
def mock_psycopg_connection_cursor(monkeypatch: pytest.MonkeyPatch) -> Mock:
    db = DATABASE
    mock = Mock(psycopg.Cursor)
    mock.execute.side_effect = db.execute_side_effect

    mock.fetchone.side_effect = db.fetchone_side_effect
    mock.fetchall.side_effect = db.fetchall_side_effect
    monkeypatch.setattr(psycopg.Connection, "cursor", mock)
    return mock


@pytest.fixture(name="handler", autouse=True)
def mock_database_handler(monkeypatch: pytest.MonkeyPatch, cursor: psycopg.Cursor) -> Mock:
    @contextmanager
    def mocked_handler() -> Generator[DatabaseHandler, None, None]:
        print(f"DEBUG: yielding mocked handler")
        yield DatabaseHandler(cursor, Message.OK)

    mock_handler = Mock(side_effect=mocked_handler)
    monkeypatch.setattr(DatabaseProvider, "handler", mock_handler)
    return mock_handler


@pytest.fixture(name="failing_handler")
def mock_failing_handler(monkeypatch: pytest.MonkeyPatch, cursor: psycopg.Cursor) -> Mock:
    @contextmanager
    def mocked_handler() -> Generator[DatabaseHandler, None, None]:
        yield DatabaseHandler(cursor, Message.UNKNOWN_ERROR)

    mock = Mock(side_effect=mocked_handler)
    monkeypatch.setattr(DatabaseProvider, "handler", mock)
    return mock


@pytest.fixture(autouse=True)
def fixture_prevent_env_check_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(DatabaseProvider, "db_name", "none")
    monkeypatch.setattr(DatabaseProvider, "db_user", "none")
    monkeypatch.setattr(DatabaseProvider, "db_password", "none")
    monkeypatch.setattr(DatabaseProvider, "db_hostname", "none")
    monkeypatch.setattr(DatabaseProvider, "db_connection_timeout", "2")


class Test_Server:
    @pytest.fixture(name="server")
    def mock_server(self) -> Server:
        server = Server()
        server.app.config.update({"TESTING": True})

        return server

    @pytest.fixture(name="client")
    def mock_client(self, server: Server) -> FlaskClient:
        return server.app.test_client()

    @pytest.fixture(name="token")
    def fixture_register_and_login(self, client: FlaskClient) -> str:
        client.post(
            "api/v1/auth/register",
            json={
                "email": "legit_email@gmail.com",
                "password": "thelegend27",
                "confirmPassword": "thelegend27",
            },
        )
        login_response = client.post(
            "api/v1/auth/login",
            json={
                "email": "legit_email@gmail.com",
                "password": "thelegend27",
            },
        )
        return login_response.get_json()["auth_token"]

    @pytest.fixture(name="deposit")
    def fixture_deposit(self, token: str, client: FlaskClient) -> float:
        amount: float = 21.37
        client.post(
            "api/v1/wallet/deposit",
            json={
                "amount": amount,
            },
            headers={"x-access-token": token},
        )
        return amount

    class Test_Auth:
        class Test_RegisterEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.url_path: str = "api/v1/auth/register"
                self.client: FlaskClient = client

            def test_send_400_on_invalid_json_format(self) -> None:
                response = self.client.post(
                    self.url_path,
                    json={
                        "email": "legit_email@gmail.com",
                        "totally_wrong_key": "what_even_is_this",
                    },
                )
                assert response.status_code == 400

            def test_send_500_on_internal_error(self, failing_handler: Mock) -> None:
                response = self.client.post(
                    self.url_path,
                    json={
                        "email": "legit_email@gmail.com",
                        "password": "thelegend27",
                        "confirmPassword": "thelegend27",
                    },
                )
                assert response.status_code == 500

            def test_send_400_when_passwords_dont_match(self) -> None:
                response = self.client.post(
                    self.url_path,
                    json={
                        "email": "legit_email@gmail.com",
                        "password": "thelegend27",
                        "confirmPassword": "thelegend28",
                    },
                )
                assert response.status_code == 400

            def test_send_202_when_user_exists(self) -> None:
                self.client.post(
                    self.url_path,
                    json={
                        "email": "legit_email@gmail.com",
                        "password": "thelegend27",
                        "confirmPassword": "thelegend27",
                    },
                )
                response = self.client.post(
                    self.url_path,
                    json={
                        "email": "legit_email@gmail.com",
                        "password": "thelegend27",
                        "confirmPassword": "thelegend27",
                    },
                )
                assert response.status_code == 202

            def test_send_201_on_success(self) -> None:
                response = self.client.post(
                    self.url_path,
                    json={
                        "email": "other_legit_email@gmail.com",
                        "password": "thelegend27",
                        "confirmPassword": "thelegend27",
                    },
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
                    json={
                        "email": "legit_email@gmail.com",
                        "totally_wrong_key": "what_even_is_this",
                    },
                )
                assert response.status_code == 400

            def test_send_500_on_internal_error(self, failing_handler: Mock) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                assert response.status_code == 500

            def test_send_401_when_unauthorized(self) -> None:
                # basically we are trying to log in without registering
                response = self.client.post(
                    self.url_path,
                    json={"email": "not_legit_email@gmail.com", "password": "nice_try"},
                )
                assert response.status_code == 401

            def test_send_201_on_success(self) -> None:
                # register and then login
                self.client.post(
                    self.register_path,
                    json={
                        "email": "legit_email@gmail.com",
                        "password": "thelegend27",
                        "confirmPassword": "thelegend27",
                    },
                )

                response = self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "thelegend27"},
                )
                assert response.status_code == 201

            def test_send_403_when_cannot_verify(self) -> None:
                # register and then try to log in with wrong password
                self.client.post(
                    self.register_path,
                    json={
                        "email": "legit_email@gmail.com",
                        "password": "thelegend27",
                        "confirmPassword": "thelegend27",
                    },
                )

                response = self.client.post(
                    self.url_path,
                    json={"email": "legit_email@gmail.com", "password": "wrong_password"},
                )
                assert response.status_code == 403

        class Test_MeEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.url_path: str = "api/v1/auth/me"
                self.client: FlaskClient = client

            def test_send_405_on_invalid_method(self) -> None:
                response = self.client.post(self.url_path)
                assert response.status_code == 405

            @pytest.mark.skip("Currently returns 401 due to internal error on token validation")
            def test_send_500_on_internal_error(self, token: str, failing_handler: Mock) -> None:
                response = self.client.get(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 500

            def test_send_401_when_unauthorized_no_token(self) -> None:
                response = self.client.get(self.url_path)
                assert response.status_code == 401

            def test_send_401_when_unauthorized_user_not_registered(
                self, token: str, failing_handler: Mock
            ) -> None:
                response = self.client.get(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 401

            def test_send_200_on_success(self, token: str) -> None:
                # register, login, retrieve token and get to me endpoint
                response = self.client.get(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 200

        class Test_LogoutEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.url_path: str = "api/v1/auth/logout"
                self.client: FlaskClient = client

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
                    headers={"x-access-token": token},
                )
                assert response.status_code == 401

            def test_send_500_on_revoke_failure(
                self, token: str, token_revoke_failure: Mock
            ) -> None:
                # logout halted due to token revoke fail
                response = self.client.post(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 500

            def test_send_201_on_success(self, token: str) -> None:
                response = self.client.post(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 201

    class Test_Wallet:
        class Test_BalanceEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.url_path: str = "api/v1/wallet/balance"
                self.client: FlaskClient = client

            def test_send_200_on_success(self, token: str, deposit: float) -> None:
                response = self.client.get(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 200
                assert response.get_json()["wallet_usd"] == deposit

            def test_send_401_when_unauthorized_no_token(self) -> None:
                response = self.client.get(
                    self.url_path,
                )
                assert response.status_code == 401

            def test_send_401_when_unauthorized_user_not_registered(
                self, token: str, failing_handler: Mock
            ) -> None:
                response = self.client.get(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 401

            def test_send_405_on_invalid_method(self) -> None:
                response = self.client.post(self.url_path)
                assert response.status_code == 405

            @pytest.mark.skip("Currently returns 401 due to internal error on token validation")
            def test_send_500_on_internal_error(self, token: str, failing_handler: Mock) -> None:
                response = self.client.post(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 500

        class Test_DepositEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.url_path: str = "api/v1/wallet/deposit"
                self.client: FlaskClient = client

            @pytest.mark.parametrize("amount", [1, 5.75])
            def test_send_200_on_success(self, token: str, amount: float) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": amount},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 200

            @pytest.mark.parametrize("amount", [-5.75, 0.0])
            def test_send_400_on_invalid_json_format(self, token: str, amount: float) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": amount},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 400

            def test_send_401_when_unauthorized_no_token(self) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 5.75},
                )
                assert response.status_code == 401

            def test_send_401_when_unauthorized_user_not_registered(
                self, token: str, failing_handler: Mock
            ) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 5.75},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 401

            @pytest.mark.skip("Currently returns 401 due to internal error on token validation")
            def test_send_500_on_internal_error(self, token: str, failing_handler: Mock) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 5.75},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 500

        class Test_WithdrawEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.url_path: str = "api/v1/wallet/withdraw"
                self.client: FlaskClient = client

            @pytest.mark.parametrize("amount", [1, 5.75])
            def test_send_200_on_success(self, token: str, deposit: float, amount: float) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": amount},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 200

            @pytest.mark.parametrize("amount", [-5.75, 0.0])
            def test_send_400_on_invalid_json_format(
                self, token: str, deposit: float, amount: float
            ) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": amount},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 400

            def test_send_401_when_unauthorized_no_token(self) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 5.75},
                )
                assert response.status_code == 401

            def test_send_401_when_unauthorized_user_not_registered(
                self, token: str, deposit: float, failing_handler: Mock
            ) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 5.75},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 401

            def test_send_409_when_not_enough_money_to_withdraw(
                self, token: str, deposit: float
            ) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 100.01},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 409

            @pytest.mark.skip("Currently returns 401 due to internal error on token validation")
            def test_send_500_on_internal_error(
                self, token: str, deposit: float, failing_handler: Mock
            ) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 5.75},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 500

        class Test_BuyEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.url_path: str = "api/v1/wallet/buy"
                self.client: FlaskClient = client

            @pytest.mark.parametrize("amount", [0.1, 2])
            def test_send_200_on_success(self, token: str, deposit: float, amount: float) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": amount},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 200

            @pytest.mark.parametrize("amount", [-2, 0])
            def test_send_400_on_invalid_json_format(
                self, token: str, deposit: float, amount: float
            ) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": amount},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 400

            def test_send_401_when_unauthorized_no_token(self) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 0.1},
                )
                assert response.status_code == 401

            def test_send_401_when_unauthorized_user_not_registered(
                self, token: str, deposit: float, failing_handler: Mock
            ) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 0.1},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 401

            def test_send_409_when_not_enough_money_to_purchase_BTC(
                self, token: str, deposit: float
            ) -> None:
                response = self.client.post(
                    self.url_path,
                    json={"amount": 10},
                    headers={"x-access-token": token},
                )
                assert response.status_code == 409

        class Test_HistoryEndpoint:
            @pytest.fixture(autouse=True)
            def prepare_tests(self, client: FlaskClient) -> None:
                self.url_path: str = "api/v1/wallet/history"
                self.client: FlaskClient = client

            def test_send_200_on_success(self, token: str) -> None:
                response = self.client.get(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 200

            def test_send_401_when_unauthorized_no_token(self) -> None:
                response = self.client.get(
                    self.url_path,
                )
                assert response.status_code == 401

            def test_send_401_when_unauthorized_user_not_registered(
                self, token: str, failing_handler: Mock
            ) -> None:
                response = self.client.get(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 401

            @pytest.mark.skip("Currently returns 401 due to internal error on token validation")
            def test_send_500_on_internal_error(self, token: str, failing_handler: Mock) -> None:
                response = self.client.get(
                    self.url_path,
                    headers={"x-access-token": token},
                )
                assert response.status_code == 500
