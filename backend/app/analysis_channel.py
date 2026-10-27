"""A bounded shared-memory channel for one inference result."""

import json
from multiprocessing.context import BaseContext
from typing import Any, Protocol

MAX_WORKER_RESULT_BYTES = 1_048_576


class ResultChannel(Protocol):
    def send(self, message: dict[str, Any]) -> None: ...

    def close(self) -> None: ...


class SharedResultChannel:
    def __init__(self, context: BaseContext) -> None:
        self._buffer = context.RawArray(
            "B",
            MAX_WORKER_RESULT_BYTES,
        )
        self._length = context.RawValue("I", 0)

    def send(self, message: dict[str, Any]) -> None:
        """Write the payload, then mark how many bytes are available."""
        encoded = json.dumps(
            message,
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")

        if len(encoded) > MAX_WORKER_RESULT_BYTES:
            encoded = b'{"status":"failure"}'

        self._buffer[:len(encoded)] = encoded
        self._length.value = len(encoded)

    def receive(self) -> dict[str, Any]:
        """Read a completed payload after the worker has exited."""
        length = self._length.value
        if not 0 < length <= MAX_WORKER_RESULT_BYTES:
            raise ValueError("Worker result unavailable")

        encoded = bytes(self._buffer[:length])
        message = json.loads(encoded.decode("utf-8"))

        if not isinstance(message, dict):
            raise TypeError("Invalid worker result")

        return message

    def close(self) -> None:
        """Shared storage is released when its owning objects are released."""
