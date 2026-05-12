"""공용 로깅 설정.

main.py 외에도 import 시점에 한 번만 root logger 를 설정하고, 두 번째
호출부터는 이미 만들어진 'kiwoom' 로거를 그대로 돌려준다.

환경변수:
    KIWOOM_LOG_LEVEL: DEBUG / INFO / WARNING / ERROR (기본 INFO)

산출:
    data/main.log : 5MB rotating, 5개 백업, UTF-8.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys


LOG_DIR = "data"
LOG_FILE_NAME = "main.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE_MAX_BYTES = 5_000_000
LOG_FILE_BACKUP_COUNT = 5
LOGGER_NAME = "kiwoom"


def setup_logging() -> logging.Logger:
    """root logger 를 한 번만 초기화하고 'kiwoom' 로거를 돌려준다."""
    os.makedirs(LOG_DIR, exist_ok=True)
    root = logging.getLogger()
    if root.handlers:
        return logging.getLogger(LOGGER_NAME)

    level_name = os.environ.get("KIWOOM_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root.setLevel(level)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE_NAME),
        maxBytes=LOG_FILE_MAX_BYTES,
        backupCount=LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    return logging.getLogger(LOGGER_NAME)
