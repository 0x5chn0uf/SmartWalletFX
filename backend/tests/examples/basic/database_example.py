from app.models import User


def test_user_creation_in_db(sync_session):
    # Create a new user record
    user = User(username="bob", email="bob@example.com", hashed_password="x")
    sync_session.add(user)
    sync_session.commit()
    # Verify user exists
    result = sync_session.get(User, user.id)
    assert result is not None
