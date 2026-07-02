"""
Minimal MCP (Model Context Protocol) JSON-RPC 2.0 dispatcher.

Implements the stateless subset of the Streamable HTTP transport that
claude.ai custom connectors need: initialize, notifications/*, tools/list,
tools/call, ping. Every response is plain JSON (the SSE mode of the
transport is optional per spec and deliberately unsupported — this must
run under gunicorn WSGI).
"""
import json
import logging

logger = logging.getLogger(__name__)

SUPPORTED_PROTOCOL_VERSIONS = ('2025-06-18', '2025-03-26')
DEFAULT_PROTOCOL_VERSION = '2025-06-18'
SERVER_INFO = {'name': 'projectapp-blog-mcp', 'version': '1.0.0'}

INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class ToolError(Exception):
    """Business/validation error inside a tool handler.

    Surfaces as result.isError=true with a readable message so the calling
    model can fix its arguments and retry.
    """


def _error(msg_id, code, message):
    return 200, {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': code, 'message': message}}


def _result(msg_id, result):
    return 200, {'jsonrpc': '2.0', 'id': msg_id, 'result': result}


def _text_result(msg_id, payload, is_error=False):
    text = payload if isinstance(payload, str) else json.dumps(
        payload, ensure_ascii=False, default=str,
    )
    return _result(msg_id, {
        'content': [{'type': 'text', 'text': text}],
        'isError': is_error,
    })


def handle_message(message, tools):
    """
    Handle one JSON-RPC message. Returns (http_status, response_dict|None).
    Notifications (no 'id') return (202, None) per Streamable HTTP transport.
    """
    if not isinstance(message, dict):
        return _error(None, INVALID_REQUEST, 'Expected a single JSON-RPC request object.')

    method = message.get('method', '')
    msg_id = message.get('id')
    params = message.get('params') or {}

    if isinstance(method, str) and method.startswith('notifications/'):
        return 202, None

    if message.get('jsonrpc') != '2.0' or not method:
        return _error(msg_id, INVALID_REQUEST, 'Malformed JSON-RPC 2.0 request.')

    if method == 'initialize':
        requested = params.get('protocolVersion', '')
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else DEFAULT_PROTOCOL_VERSION
        return _result(msg_id, {
            'protocolVersion': version,
            'capabilities': {'tools': {}},
            'serverInfo': SERVER_INFO,
        })

    if method == 'ping':
        return _result(msg_id, {})

    if method == 'tools/list':
        return _result(msg_id, {
            'tools': [
                {
                    'name': t['name'],
                    'description': t['description'],
                    'inputSchema': t['input_schema'],
                }
                for t in tools
            ],
        })

    if method == 'tools/call':
        name = params.get('name', '')
        arguments = params.get('arguments') or {}
        tool = next((t for t in tools if t['name'] == name), None)
        if tool is None:
            return _error(msg_id, INVALID_PARAMS, f'Unknown tool: {name}')
        try:
            payload = tool['handler'](arguments)
        except ToolError as exc:
            logger.info('[MCP] tool %s rejected: %s', name, exc)
            return _text_result(msg_id, str(exc), is_error=True)
        except Exception:
            logger.exception('[MCP] tool %s crashed', name)
            return _text_result(
                msg_id,
                'Error interno ejecutando la herramienta. Revisa los logs del servidor.',
                is_error=True,
            )
        logger.info('[MCP] tool %s executed ok', name)
        return _text_result(msg_id, payload)

    return _error(msg_id, METHOD_NOT_FOUND, f'Method not supported: {method}')
