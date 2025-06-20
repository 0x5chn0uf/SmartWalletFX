import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from app.domain.errors import InvalidCredentialsError
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService, DuplicateError

pytestmark = pytest.mark.anyio

char_set = st.characters(
    min_codepoint=33, max_codepoint=126
)  # printable ASCII excluding space & control


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(st.text(alphabet=char_set, min_size=8, max_size=32))
async def test_authenticate_random_passwords_fail(db_session, random_password):  # type: ignore[arg-type]
    """Random passwords that do NOT match should raise InvalidCredentialsError."""

    svc = AuthService(db_session)
    pw = "Secur3Pwd!@#"  # fixed good password
    user = UserCreate(username="charlie", email="charlie@example.com", password=pw)
    try:
        await svc.register(user)
    except DuplicateError:
        # User already exists from a previous Hypothesis example; that's fine.
        pass

    # ensure random_password is different from pw
    assume(random_password != pw)

    with pytest.raises(InvalidCredentialsError):
        await svc.authenticate("charlie", random_password)
