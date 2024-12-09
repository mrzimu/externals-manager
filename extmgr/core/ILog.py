import logging


class ILog:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.name if hasattr(self, 'name') else self.__class__.__name__)

    def debug(self, msg: str) -> None:
        self._logger.debug(msg)

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def warn(self, msg: str) -> None:
        self._logger.warning(msg)

    def error(self, msg: str) -> None:
        self._logger.error(msg)

    def fatal(self, msg: str) -> None:
        self._logger.fatal(msg)
