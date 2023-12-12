import logging
_logger = logging.getLogger(__name__)


class Authorizable:
    """Mixin for authorizable objects, to provide authorization checks.

    Subclasses must set the class var ``_AUTHORIZATION_ERROR_CLS`` and must
    implement :meth:`._check_authorization`.

    Note that ``_AUTHORIZATION_ERROR_CLS`` can be either a single exception
    class, or a tuple of them. It is only used as part of an ``except``
    catch.
    """
    _AUTHORIZATION_ERROR_CLS = None

    def _check_authorization(self) -> bool:
        """Check the authorization for this object.

        If authorization succeeds, this should return True. If authorization
        fails, this should raise ``self._AUTHORIZATION_ERROR_CLS``.
        """
        raise NotImplementedError()

    def validate_authorization(self, logger=_logger, label=None):
        """Validate the authorization for this object.

        This catches the errors raised on authorization failure, ensuring
        that a failed authorization returns ``False``. This also logs the
        failures at log level CRITICAL to the given ``logger`` (unless
        ``logger`` is ``None``).

        Parameters
        ----------
        """
        if label is None:
            label = self.__class__.__name__

        try:
            authorized = self._check_authorization()
        except self._AUTHORIZATION_ERROR_CLS as e:
            authorized = False
            if logger is not None:
                logger.critical(f"{label}: Authorization failed")
                logger.critical(f"{e.__class__.__name__}: {str(e)}")

        return authorized
