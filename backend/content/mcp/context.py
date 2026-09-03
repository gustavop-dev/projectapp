from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class McpExecutionContext:
    connector: Any
    credential: Any
    request_id: str
    actor: Any = None
    request: Any = None
    protocol_version: str = ''
    confirmation_bypass: bool = False


_current_context = ContextVar('mcp_execution_context', default=None)


def current_mcp_context():
    return _current_context.get()


@contextmanager
def use_mcp_context(context):
    token = _current_context.set(context)
    try:
        yield context
    finally:
        _current_context.reset(token)


@contextmanager
def bypass_confirmation():
    context = current_mcp_context()
    if context is None:
        yield None
        return
    token = _current_context.set(replace(context, confirmation_bypass=True))
    try:
        yield _current_context.get()
    finally:
        _current_context.reset(token)
