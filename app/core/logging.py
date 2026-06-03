import logging
import sys
from app.core.config import settings

def setup_logging() -> None:
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s |%(message)s",
        datefmt="%Y-%m-%d %H-%M-%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if logging.DEBUG else logging.WARNING
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

def get_logger(name:str) -> logging.Logger:
    return logging.getLogger(name)
