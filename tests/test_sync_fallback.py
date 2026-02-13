import json
import pytest

from src.infrastructure.sync_manager import SyncManager


class DummySecretsManager:
    def __init__(self):
        # single record with owner_name present locally
        self._data = [
            {
                "id": "abc-1",
                "service": "svc",
                "username": "user",
                "secret_blob": b"ctxt",
                "nonce_blob": b"nonce",
                "notes": "n",
                "owner_name": "OWN"
            }
        ]

    def get_all_encrypted(self):
        return self._data

    def add_secret_encrypted(self, *args, **kwargs):
        # no-op for restore
        return True


class FakeResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


def test_backup_retries_without_owner_name(monkeypatch):
    sm = DummySecretsManager()
    manager = SyncManager(sm, "http://example.com", "KEY")

    # Force internet available
    monkeypatch.setattr(manager, "_has_internet", lambda: True)

    calls = []

    # First call: return 400 with PGRST204-like message
    # Second call: return 201 success and record payload
    responses = [
        FakeResponse(400, "PGRST204: Could not find the 'owner_name' column of 'secrets' in the schema cache"),
        FakeResponse(201, "OK")
    ]

    # Also mock the initial probe GET for owner_name to return a 400 (simulate missing)
    def fake_get(url, headers=None, timeout=5):
        return FakeResponse(400, "PGRST204: Could not find the 'owner_name' column of 'secrets' in the schema cache")

    monkeypatch.setattr("requests.get", fake_get)

    def fake_post(url, headers=None, data=None):
        calls.append(json.loads(data))
        return responses.pop(0)

    monkeypatch.setattr("requests.post", fake_post)

    # Run backup; should not raise and should have tried twice
    manager.backup_to_supabase()

    assert len(calls) == 2
    # First call payload contains owner_name
    first = calls[0][0]
    assert "owner_name" in first
    # Second call payload should not contain owner_name
    second = calls[1][0]
    assert "owner_name" not in second
