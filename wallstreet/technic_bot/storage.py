"""
aiogram FSM storage — Django ORM (enrollments.BotFSMState) ustida.

Texnik bot asosiy botdan alohida `bot_id` ga ega bo'lgani uchun kalitlar
to'qnashmaydi — ikkala bot ham bitta jadvalni xavfsiz ishlatadi.
"""
from collections.abc import Mapping
from typing import Any

from asgiref.sync import sync_to_async

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey


def _key_str(key: StorageKey) -> str:
    return ":".join(str(p) for p in (
        key.bot_id,
        key.chat_id,
        key.thread_id or 0,
        key.user_id,
        key.business_connection_id or "",
        key.destiny,
    ))


@sync_to_async
def _row(key_str: str):
    from enrollments.models import BotFSMState
    return BotFSMState.objects.filter(key=key_str).values("state", "data").first()


@sync_to_async
def _write_state(key_str: str, state: str):
    from enrollments.models import BotFSMState
    obj, _ = BotFSMState.objects.get_or_create(key=key_str)
    obj.state = state or ""
    obj.save(update_fields=["state", "updated_at"])


@sync_to_async
def _write_data(key_str: str, data: dict):
    from enrollments.models import BotFSMState
    obj, _ = BotFSMState.objects.get_or_create(key=key_str)
    obj.data = data or {}
    obj.save(update_fields=["data", "updated_at"])


class DjangoFSMStorage(BaseStorage):
    async def set_state(self, key: StorageKey, state=None) -> None:
        state_str = state.state if isinstance(state, State) else state
        await _write_state(_key_str(key), state_str or "")

    async def get_state(self, key: StorageKey):
        row = await _row(_key_str(key))
        if not row:
            return None
        return row["state"] or None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        await _write_data(_key_str(key), dict(data))

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        row = await _row(_key_str(key))
        if not row:
            return {}
        return dict(row["data"] or {})

    async def close(self) -> None:
        pass
