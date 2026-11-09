import asyncio
import os
import runpy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import config
import handlers


def callback(action: str):
    return SimpleNamespace(
        data=action,
        from_user=SimpleNamespace(id=42),
        message=SimpleNamespace(chat=SimpleNamespace(type="private", id=42)),
        answer=AsyncMock(),
    )


@pytest.mark.parametrize("action", [
    "admin_statistic", "global_message", "create_db_archive", "make_dict", "collate",
    "add_admin:43", "remove_admin:43", "block_user:43", "give_premium:43",
    "delete_from_database_user:43", "add_access:43", "remove_access:43",
])
def test_admin_callbacks_require_current_permission(monkeypatch, action):
    monkeypatch.setattr(handlers, "is_user_blocked", AsyncMock(return_value=False))
    monkeypatch.setattr(handlers, "is_user_admin", AsyncMock(return_value=False))
    event = callback(action)
    state = SimpleNamespace(update_data=AsyncMock())
    asyncio.run(handlers.callbacks(event, state))
    event.answer.assert_awaited_once_with("Недостаточно прав.", show_alert=True)
    state.update_data.assert_not_awaited()


def test_subscription_lookup_is_scoped_to_requesting_user(monkeypatch):
    monkeypatch.setattr(handlers, "is_user_blocked", AsyncMock(return_value=False))
    lookup = AsyncMock(return_value=None)
    monkeypatch.setattr(handlers, "get_subscription_details", lookup)
    remove = AsyncMock()
    monkeypatch.setattr(handlers, "remove_subscriptions", remove)
    event = callback("subscription:17")
    asyncio.run(handlers.callbacks(event, SimpleNamespace()))
    lookup.assert_awaited_once_with(17, 42)
    remove.assert_not_awaited()


def test_revoked_admin_cannot_send_broadcast(monkeypatch):
    monkeypatch.setattr(handlers, "is_user_admin", AsyncMock(return_value=False))
    send = AsyncMock()
    monkeypatch.setattr(handlers.BOT, "send_message", send)
    event = SimpleNamespace(from_user=SimpleNamespace(id=42), answer=AsyncMock(), text="text")
    state = SimpleNamespace(clear=AsyncMock())
    asyncio.run(handlers.global_message(event, state))
    send.assert_not_awaited()
    state.clear.assert_awaited_once()


def test_missing_configuration_does_not_expose_value(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN")
    with pytest.raises(ValueError, match="BOT_TOKEN"):
        config.required("BOT_TOKEN")


def test_webhook_origin_rejects_plain_http(monkeypatch):
    monkeypatch.setenv("BASE_WEBHOOK_URL", "http://example.invalid")
    with pytest.raises(ValueError, match="HTTPS origin"):
        runpy.run_path("config.py")


def test_env_initialization_preserves_existing_file(tmp_path, monkeypatch):
    module = runpy.run_path("scripts/init_env.py")
    monkeypatch.chdir(tmp_path)
    Path(".env.example").write_text("BOT_TOKEN=\nWEBHOOK_SECRET=\n", encoding="utf-8")
    module["main"]()
    target = Path(".env")
    before = target.read_bytes()
    assert os.stat(target).st_mode & 0o777 == 0o600
    assert len(before.split(b"WEBHOOK_SECRET=", 1)[1].strip()) >= 32
    with pytest.raises(SystemExit, match="уже существует"):
        module["main"]()
    assert target.read_bytes() == before
