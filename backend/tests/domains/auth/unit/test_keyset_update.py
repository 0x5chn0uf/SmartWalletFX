from app.utils.jwt_rotation import KeySetUpdate


def test_is_noop_conditions():
    """Verify the is_noop helper across combinations."""
    assert KeySetUpdate().is_noop() is True
    assert KeySetUpdate(new_active_kid="k").is_noop() is False
    assert KeySetUpdate(keys_to_retire={"a"}).is_noop() is False
