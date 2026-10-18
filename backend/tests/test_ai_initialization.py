from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock

from backend.ai import local_provider
from backend.app import main


def test_concurrent_first_requests_share_local_provider(monkeypatch):
    constructing = Event()
    release = Event()
    contending = Event()
    constructed = []
    lock = Lock()

    class ObservedLock:
        def __enter__(self):
            if lock.locked():
                contending.set()
            lock.acquire()

        def __exit__(self, *_args):
            lock.release()

    class FakeProvider:
        def __init__(self, **_kwargs):
            constructed.append(self)
            constructing.set()
            assert release.wait(5)

    monkeypatch.setattr(main, "get_ai_config", lambda: ("local", None, None))
    monkeypatch.setattr(main, "_ai_service_lock", ObservedLock())
    monkeypatch.setattr(local_provider, "LocalProvider", FakeProvider)
    main._get_cached_ai_service.cache_clear()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(main.get_ai_service)
            try:
                assert constructing.wait(5)
                second = pool.submit(main.get_ai_service)
                assert contending.wait(5)
            finally:
                release.set()
            assert first.result(timeout=5) is second.result(timeout=5)
            assert len(constructed) == 1
    finally:
        main._get_cached_ai_service.cache_clear()


def test_failed_initialization_can_be_retried(monkeypatch):
    attempts = []

    def config():
        attempts.append(None)
        if len(attempts) == 1:
            raise RuntimeError("Temporary configuration failure")
        return "mock", None, None

    import pytest

    monkeypatch.setattr(main, "get_ai_config", config)
    main._get_cached_ai_service.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="Temporary configuration failure"):
            main.get_ai_service()
        service = main.get_ai_service()
        assert service[1] == "mock"
        assert main.get_ai_service() is service
        assert len(attempts) == 2
    finally:
        main._get_cached_ai_service.cache_clear()
