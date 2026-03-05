import logging


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    root_logger = logging.getLogger()

    if root_logger.handlers:
        root_logger.setLevel(level)
        return

    logging.basicConfig(level=level, format=LOG_FORMAT)
