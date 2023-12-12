import os

import smtplib
import imaplib
import github

import logging
_logger = logging.getLogger(__name__)

from .task import Task

class AuthorizationCheck(Task):
    """Task to test whether authorization is configured correctly."""
    CONFIG = "authorization-check"

    @staticmethod
    def _validate_secret_exists(secret_name, level=logging.CRITICAL):
        """
        Parameters
        ----------
        secret_name : str
            the name of the environment variable where the secret should be
            stored
        level : int
            level at which to log message if the environment variable is
            missing
        """
        secret = os.environ.get(secret_name)
        if not secret:
            _logger.log(
                level,
                f"Missing environment variable ${secret_name}.\n"
                "Likely causes:\n"
                " * GitHub secret of that name missing\n"
                " * Spelling mismatch between the config name and the "
                "GitHub secret"
            )
        return bool(secret)

    def _run(self, config, dry):
        _logger.debug(f"CONFIG: {config}")

        # check bot token
        valid_bot = (
            self._validate_secret_exists(self.bot.token_secret)
            and self.bot.validate_authorization(logger=_logger)
        )

        # check SMTP token
        if smtp_secret_name := getattr(self.bot.smtp, 'secret', None):
            # bot.smtp.secret is defined; check if it exists
            valid_smtp = (
                self._validate_secret_exists(smtp_secret_name)
                and self.bot.smtp.validate_authorization(logger=_logger,
                                                         label="Bot SMTP")
            )
        else:
            # bot.smtp.secret not defined; warn, but call it valid because
            # this isn't actually an error
            valid_smtp = True
            _logger.warn("No SMTP secret defined; sendmail not possible")

        # check inbox secret
        valid_inbox = (
            self._validate_secret_exists(self.inbox.secret)
            and self.inbox.validate_authorization(logger=_logger,
                                                  label="Inbox")
        )

        if not (valid_bot and valid_smtp and valid_inbox):
            return 1

    def _build_config(self):
        return self.config


if __name__ == "__main__":
    AuthorizationCheck.run_cli()
