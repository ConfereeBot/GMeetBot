from enum import StrEnum


class Res(StrEnum):
    STARTED = "started"
    ERROR = "error"
    SUCCEDED = "succeded"
    BUSY = "busy"


class Req(StrEnum):
    SCREENSHOT = "screenshot"
    TIME = "time"


def prepare(res: Res, body, filepath="") -> bytes:
    return str({"type": res.value, "body": body, "filepath": filepath}).encode()
