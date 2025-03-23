from enum import StrEnum


class Res(StrEnum):
    """Ответ коньюмера."""

    STARTED = "started"
    ERROR = "error"
    SUCCEDED = "succeded"
    BUSY = "busy"


class Req(StrEnum):
    """Запрос продюсера."""

    SCREENSHOT = "screenshot"
    TIME = "time"
    STOP_RECORD = "stop"


def prepare(res: Res, body, user_id: int = -1, filepath: str = "") -> bytes:
    """Создание сообщения в очередь."""
    return str(
        {
            "type": res.value,
            "body": body,
            "user_id": user_id,
            "filepath": filepath,
        }
    ).encode()
