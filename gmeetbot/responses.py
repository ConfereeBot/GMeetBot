from enum import StrEnum


class Res(StrEnum):
    STARTED = "started"
    ERROR = "error"
    SUCCEDED = "succeded"
    BUSY = "busy"


class Req(StrEnum):
    SCREENSHOT = "screenshot"
    TIME = "time"


def prepare(res: Res, body) -> bytes:
    return str({"res": res, "body": body}).encode()
