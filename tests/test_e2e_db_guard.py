import pytest

from scripts.e2e_db_guard import UnsafeE2EDatabaseError, assert_safe_e2e_database_url

_DEV_DEFAULT_URL = "postgresql://postgres:devpassword@localhost:5433/aimx"


def test_3b_db_01_missing_url_refuses() -> None:
    with pytest.raises(UnsafeE2EDatabaseError):
        assert_safe_e2e_database_url("")


def test_3b_db_01_whitespace_only_url_refuses() -> None:
    with pytest.raises(UnsafeE2EDatabaseError):
        assert_safe_e2e_database_url("   ")


def test_3b_db_02_normal_developer_url_refuses_via_ambient_match() -> None:
    with pytest.raises(UnsafeE2EDatabaseError):
        assert_safe_e2e_database_url(_DEV_DEFAULT_URL, ambient_default_url=_DEV_DEFAULT_URL)


def test_3b_db_02_normal_developer_url_refuses_via_missing_marker() -> None:
    # Even without an ambient comparison, a database name lacking the "e2e"
    # marker must never be treated as approved.
    with pytest.raises(UnsafeE2EDatabaseError):
        assert_safe_e2e_database_url(_DEV_DEFAULT_URL)


def test_3b_db_03_approved_e2e_url_allows() -> None:
    assert_safe_e2e_database_url(
        "postgresql://postgres:devpassword@localhost:5433/aimx_e2e",
        ambient_default_url=_DEV_DEFAULT_URL,
    )


def test_3b_db_03_approved_e2e_url_allows_without_ambient_supplied() -> None:
    assert_safe_e2e_database_url("postgresql://postgres:devpassword@localhost:5433/aimx_e2e")


def test_3b_db_04_malformed_url_refuses_non_postgres_scheme() -> None:
    with pytest.raises(UnsafeE2EDatabaseError):
        assert_safe_e2e_database_url("mysql://user:pass@localhost:3306/aimx_e2e")


def test_3b_db_04_malformed_url_refuses_missing_scheme() -> None:
    with pytest.raises(UnsafeE2EDatabaseError):
        assert_safe_e2e_database_url("not-a-url-at-all")


def test_3b_db_04_malformed_url_refuses_missing_database_name() -> None:
    with pytest.raises(UnsafeE2EDatabaseError):
        assert_safe_e2e_database_url("postgresql://postgres:devpassword@localhost:5433/")


def test_3b_db_04_malformed_url_refuses_missing_host() -> None:
    with pytest.raises(UnsafeE2EDatabaseError):
        assert_safe_e2e_database_url("postgresql:///aimx_e2e")
