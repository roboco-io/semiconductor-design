from unittest.mock import patch, MagicMock
from semi_design_runner.aws.clients import make_session, make_client


def test_make_session_uses_named_profile():
    with patch("boto3.Session") as MockSession:
        make_session(profile="test-profile")
        MockSession.assert_called_once_with(profile_name="test-profile")


def test_make_session_allows_none_profile():
    with patch("boto3.Session") as MockSession:
        make_session(profile=None)
        MockSession.assert_called_once_with(profile_name=None)


def test_make_client_applies_retry_config():
    with patch("boto3.Session") as MockSession:
        mock_session = MagicMock()
        MockSession.return_value = mock_session
        make_client("s3", profile="p")
        args, kwargs = mock_session.client.call_args
        assert args[0] == "s3"
        assert kwargs["config"].retries["max_attempts"] == 5
        assert kwargs["config"].retries["mode"] == "adaptive"
