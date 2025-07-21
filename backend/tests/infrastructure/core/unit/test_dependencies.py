import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, Request
from redis import Redis

from app.api.dependencies import (
    AuthDeps,
    AuthorizationDeps,
    auth_deps,
    get_redis,
    get_user_from_request,
    get_user_id_from_request,
    has_permission,
    require_attributes,
    require_permission,
    require_roles,
)
from app.core.security.roles import UserRole


class DummyUser:
    def __init__(self, id):
        self.id = id


class DummySession:  # noqa: D101 – async session stub
    def __init__(self, user: DummyUser | None):
        self._user = user

    async def get(self, model, pk):  # noqa: D401 – mimic SQLAlchemy AsyncSession.get
        if self._user and self._user.id == pk:
            return self._user
        return None


@pytest.mark.asyncio
async def test_get_user_from_request_success():
    """A valid user_id and token payload on request state returns the user instance."""
    user_id = uuid.uuid4()
    user = DummyUser(id=user_id)
    session = DummySession(user)

    payload = {"sub": str(user_id), "roles": ["user"], "attributes": {}}
    request = Mock(state=Mock(user_id=user_id, token_payload=payload))

    # Mock the DIContainer and database service
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__.return_value = session

    mock_database = Mock()
    mock_database.get_session.return_value = mock_session_context

    mock_di_container = Mock()
    mock_di_container.get_core.return_value = mock_database

    with patch("app.main.di_container", mock_di_container):
        result = await get_user_from_request(request=request)

        assert result is user
        assert hasattr(result, "_current_roles")
        assert result._current_roles == ["user"]
        assert hasattr(result, "_current_attributes")
        assert result._current_attributes == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, token_payload, session_user, expected_detail",
    [
        (None, {"sub": "test", "roles": []}, None, "Not authenticated"),
        (uuid.uuid4(), None, None, "Not authenticated"),
        (uuid.uuid4(), {"sub": "test", "roles": []}, None, "User not found"),
    ],
)
async def test_get_user_from_request_error_paths(
    user_id, token_payload, session_user, expected_detail
):
    """Verify each error branch raises HTTPException with the correct detail message."""
    request = Mock(state=Mock(user_id=user_id, token_payload=token_payload))
    session = DummySession(user=session_user)

    # Mock the DIContainer and database service
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__.return_value = session

    mock_database = Mock()
    mock_database.get_session.return_value = mock_session_context

    mock_di_container = Mock()
    mock_di_container.get_core.return_value = mock_database

    with patch("app.main.di_container", mock_di_container):
        with pytest.raises(HTTPException) as exc:
            await get_user_from_request(request=request)

        assert exc.value.status_code == 401
        assert expected_detail in exc.value.detail


class TestAuthDeps:
    """Test AuthDeps class."""

    def test_auth_deps_init(self):
        """Test AuthDeps initialization."""
        deps = AuthDeps()
        assert deps.config is not None

    @pytest.mark.asyncio
    async def test_rate_limit_auth_token_success(self):
        """Test rate limiting allows request when under limit."""
        deps = AuthDeps()
        request = Mock()
        request.client.host = "127.0.0.1"

        # Mock rate limiter to allow request
        with patch("app.api.dependencies.login_rate_limiter") as mock_limiter:
            mock_limiter.allow.return_value = True

            # Should not raise exception
            await deps.rate_limit_auth_token(request)
            mock_limiter.allow.assert_called_once_with("127.0.0.1")

    @pytest.mark.asyncio
    async def test_rate_limit_auth_token_no_client_host(self):
        """Test rate limiting handles missing client host."""
        deps = AuthDeps()
        request = Mock()
        request.client.host = None

        with patch("app.api.dependencies.login_rate_limiter") as mock_limiter:
            mock_limiter.allow.return_value = True

            await deps.rate_limit_auth_token(request)
            mock_limiter.allow.assert_called_once_with("unknown")

    @pytest.mark.asyncio
    async def test_rate_limit_auth_token_exceeds_limit(self):
        """Test rate limiting raises exception when limit exceeded."""
        deps = AuthDeps()
        request = Mock()
        request.client.host = "127.0.0.1"

        with patch("app.api.dependencies.login_rate_limiter") as mock_limiter:
            mock_limiter.allow.return_value = False

            with pytest.raises(HTTPException) as exc:
                await deps.rate_limit_auth_token(request)

            assert exc.value.status_code == 429
            assert "Too many login attempts" in exc.value.detail
            assert "Retry-After" in exc.value.headers


def test_get_user_id_from_request_success():
    """Test get_user_id_from_request with valid user_id."""
    user_id = uuid.uuid4()
    request = Mock()
    request.state.user_id = user_id

    result = get_user_id_from_request(request)
    assert result == user_id


def test_get_user_id_from_request_no_user_id():
    """Test get_user_id_from_request raises exception when no user_id."""
    request = Mock()
    request.state.user_id = None

    with pytest.raises(HTTPException) as exc:
        get_user_id_from_request(request)

    assert exc.value.status_code == 401
    assert "Not authenticated" in exc.value.detail


@pytest.mark.asyncio
async def test_get_redis():
    """Test get_redis context manager."""
    mock_client = Mock(spec=Redis)
    mock_client.close = AsyncMock()

    with patch("app.api.dependencies._build_redis_client", return_value=mock_client):
        redis_gen = get_redis()
        client = await redis_gen.__anext__()
        assert client is mock_client

        try:
            await redis_gen.__anext__()
        except StopAsyncIteration:
            pass

        mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_get_redis_with_exception():
    """Test get_redis handles close exception gracefully."""
    mock_client = Mock(spec=Redis)
    mock_client.close = AsyncMock(side_effect=Exception("Close error"))

    with patch("app.api.dependencies._build_redis_client", return_value=mock_client):
        redis_gen = get_redis()
        client = await redis_gen.__anext__()
        assert client is mock_client

        # Should not raise exception even if close fails
        try:
            await redis_gen.__anext__()
        except StopAsyncIteration:
            pass

        mock_client.close.assert_called_once()


class TestAuthorizationDeps:
    """Test AuthorizationDeps class."""

    def test_ensure_list_with_list(self):
        """Test _ensure_list with list input."""
        deps = AuthorizationDeps()
        result = deps._ensure_list(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_ensure_list_with_single_value(self):
        """Test _ensure_list with single value."""
        deps = AuthorizationDeps()
        result = deps._ensure_list("single")
        assert result == ["single"]

    def test_match_attribute_simple_equality(self):
        """Test _match_attribute with simple equality."""
        deps = AuthorizationDeps()
        assert deps._match_attribute("test", "test") is True
        assert deps._match_attribute("test", "other") is False

    @pytest.mark.parametrize(
        "op,value,requirement,expected",
        [
            ("eq", 5, 5, True),
            ("eq", 5, 6, False),
            ("neq", 5, 6, True),
            ("neq", 5, 5, False),
            ("gt", 5, 4, True),
            ("gt", 5, 6, False),
            ("gte", 5, 5, True),
            ("gte", 5, 6, False),
            ("lt", 5, 6, True),
            ("lt", 5, 4, False),
            ("lte", 5, 5, True),
            ("lte", 5, 4, False),
            ("in", 5, [3, 4, 5], True),
            ("in", 5, [1, 2, 3], False),
            ("not_in", 5, [1, 2, 3], True),
            ("not_in", 5, [3, 4, 5], False),
            ("invalid", 5, 5, False),
        ],
    )
    def test_match_attribute_with_operators(self, op, value, requirement, expected):
        """Test _match_attribute with various operators."""
        deps = AuthorizationDeps()
        req = {"op": op, "value": requirement}
        assert deps._match_attribute(value, req) is expected

    def test_expand_permissions(self):
        """Test _expand_permissions with valid roles."""
        deps = AuthorizationDeps()
        roles = [UserRole.ADMIN.value, UserRole.INDIVIDUAL_INVESTOR.value]
        permissions = deps._expand_permissions(roles)
        assert isinstance(permissions, set)
        assert len(permissions) > 0

    def test_expand_permissions_invalid_role(self):
        """Test _expand_permissions with invalid role."""
        deps = AuthorizationDeps()
        roles = ["invalid_role"]
        permissions = deps._expand_permissions(roles)
        assert isinstance(permissions, set)
        assert len(permissions) == 0

    def test_has_permission_success(self):
        """Test has_permission with valid permission."""
        deps = AuthorizationDeps()
        roles = [UserRole.ADMIN.value]
        # Admin should have some permissions
        permissions = deps._expand_permissions(roles)
        if permissions:
            first_permission = next(iter(permissions))
            assert deps.has_permission(roles, first_permission) is True

    def test_has_permission_failure(self):
        """Test has_permission with invalid permission."""
        deps = AuthorizationDeps()
        roles = [UserRole.INDIVIDUAL_INVESTOR.value]
        assert deps.has_permission(roles, "non_existent_permission") is False

    def test_require_roles_success(self):
        """Test require_roles dependency with valid roles."""
        deps = AuthorizationDeps()
        required_roles = [UserRole.ADMIN.value]
        dependency = deps.require_roles(required_roles)

        request = Mock()
        request.state.token_payload = {
            "roles": [UserRole.ADMIN.value],
            "sub": "test_user",
        }

        result = dependency(request)
        assert result is request

    def test_require_roles_no_payload(self):
        """Test require_roles dependency with no token payload."""
        deps = AuthorizationDeps()
        required_roles = [UserRole.ADMIN.value]
        dependency = deps.require_roles(required_roles)

        request = Mock()
        request.state.token_payload = None

        with pytest.raises(HTTPException) as exc:
            dependency(request)

        assert exc.value.status_code == 401
        assert "Not authenticated" in exc.value.detail

    def test_require_roles_insufficient_roles(self):
        """Test require_roles dependency with insufficient roles."""
        deps = AuthorizationDeps()
        required_roles = [UserRole.ADMIN.value]
        dependency = deps.require_roles(required_roles)

        request = Mock()
        request.state.token_payload = {
            "roles": [UserRole.INDIVIDUAL_INVESTOR.value],
            "sub": "test_user",
        }

        with pytest.raises(HTTPException) as exc:
            dependency(request)

        assert exc.value.status_code == 403
        assert "Access denied" in exc.value.detail

    def test_require_attributes_success(self):
        """Test require_attributes dependency with valid attributes."""
        deps = AuthorizationDeps()
        requirements = {"region": "US", "verified": True}
        dependency = deps.require_attributes(requirements)

        request = Mock()
        request.state.token_payload = {
            "attributes": {"region": "US", "verified": True},
            "sub": "test_user",
        }

        result = dependency(request)
        assert result is request

    def test_require_attributes_no_payload(self):
        """Test require_attributes dependency with no token payload."""
        deps = AuthorizationDeps()
        requirements = {"region": "US"}
        dependency = deps.require_attributes(requirements)

        request = Mock()
        request.state.token_payload = None

        with pytest.raises(HTTPException) as exc:
            dependency(request)

        assert exc.value.status_code == 401
        assert "Not authenticated" in exc.value.detail

    def test_require_attributes_missing_attribute(self):
        """Test require_attributes dependency with missing attribute."""
        deps = AuthorizationDeps()
        requirements = {"region": "US"}
        dependency = deps.require_attributes(requirements)

        request = Mock()
        request.state.token_payload = {
            "attributes": {"other_attr": "value"},
            "sub": "test_user",
        }

        with pytest.raises(HTTPException) as exc:
            dependency(request)

        assert exc.value.status_code == 403
        assert "Access denied" in exc.value.detail
        assert "region" in exc.value.detail

    def test_require_permission_success(self):
        """Test require_permission dependency with valid permission."""
        deps = AuthorizationDeps()

        with patch.object(deps, "has_permission", return_value=True):
            dependency = deps.require_permission("read:wallets")

            request = Mock()
            request.state.token_payload = {
                "roles": [UserRole.ADMIN.value],
                "sub": "test_user",
            }

            result = dependency(request)
            assert result is request

    def test_require_permission_no_payload(self):
        """Test require_permission dependency with no token payload."""
        deps = AuthorizationDeps()
        dependency = deps.require_permission("read:wallets")

        request = Mock()
        request.state.token_payload = None

        with pytest.raises(HTTPException) as exc:
            dependency(request)

        assert exc.value.status_code == 401
        assert "Not authenticated" in exc.value.detail

    def test_require_permission_insufficient_permission(self):
        """Test require_permission dependency with insufficient permission."""
        deps = AuthorizationDeps()

        with patch.object(deps, "has_permission", return_value=False), patch.object(
            deps, "_expand_permissions", return_value=set()
        ):
            dependency = deps.require_permission("admin:delete")

            request = Mock()
            request.state.token_payload = {
                "roles": [UserRole.INDIVIDUAL_INVESTOR.value],
                "sub": "test_user",
            }

            with pytest.raises(HTTPException) as exc:
                dependency(request)

            assert exc.value.status_code == 403
            assert "Access denied" in exc.value.detail
            assert "admin:delete" in exc.value.detail
