import pytest

import logging
_logger = logging.getLogger(__name__)

from ticgithub.bot import *

from .utils import get_envvars_or_skip


@pytest.fixture
def realsmtp():
    user, host, secret = get_envvars_or_skip(
        "BOT_SMTP_USER",
        "BOT_SMTP_HOST",
        "BOT_SMTP_SECRET_NAME",
    )
    return SMTP(host, user, secret)


@pytest.fixture
def realbot(realsmtp):
    token_secret_name, repo = get_envvars_or_skip(
        "BOT_TOKEN_SECRET_NAME",
        "BOT_DEMO_REPO",
    )
    return Bot(token_secret_name, repo, realsmtp)


class TestSMTP:
    @pytest.mark.parametrize("auth", [True, False])
    def test_check_authorization(self, realsmtp, auth):
        if auth is False:
            realsmtp.secret = "foo"

        with caplog.at_level(logging.INFO, logger=__name__):
            result = realsmtp.validate_authorization(logger=logger,
                                                     label="Bot SMTP")
            assert result is auth
            if auth:
                expected = "Bot SMTP: Authorization succeeded"
                assert len(caplog.records) == 1
                assert expected in caplog.text
            else:
                expected_1 = "Bot SMTP: Authorization failed"
                # expected_2 = ""
                assert len(caplog.records) == 2
                assert expected_1 in caplog.text
                ... # expected_2 as well!

class TestBot:
    ...

    def test_check_authorization(self, realbot):
        ...
