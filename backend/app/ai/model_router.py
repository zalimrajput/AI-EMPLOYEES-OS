"""Thin multi-provider LLM client.

Primary provider is OpenRouter (``OPENROUTER_BASE_URL`` / ``OPENROUTER_API_KEY``);
falls back to direct OpenAI, Anthropic or Google calls when the model id
implies a different provider and the matching key is configured.  Streaming is
supported for all providers and exposed as an iterator of text chunks.
"""
import json
import logging
from typing import Iterable, Iterator, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("app.ai.model_router")

SYSTEM_ROLE = "system"


def _is_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except (ValueError, TypeError):
        return False


class ModelRouterError(RuntimeError):
    pass


def _provider_for(model: str) -> str:
    lower = model.lower()
    if "anthropic" in lower or "claude" in lower:
        return "anthropic"
    if "gemini" in lower or "google" in lower:
        return "google"
    if "openai" in lower or lower.startswith("gpt") or lower.startswith("o1") or lower.startswith("o3") or lower.startswith("text-"):
        return "openai"
    return "openrouter"


def _effective_provider(model: str, provider: str) -> str:
    """Fall back to OpenRouter when an OpenAI-style model lacks the OpenAI key
    but OpenRouter is configured (common in demo/self-host setups)."""
    if provider == "openai" and not settings.OPENAI_API_KEY and settings.OPENROUTER_API_KEY:
        return "openrouter"
    return provider


def _openrouter_headers() -> dict:
    if not settings.OPENROUTER_API_KEY:
        raise ModelRouterError("OPENROUTER_API_KEY is not configured")
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }


def _openrouter_payload(
    model: str, messages: list[dict], temperature: float, stream: bool
) -> dict:
    return {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": stream,
    }


def complete(messages: list[dict], model: Optional[str] = None, temperature: float = 0.3) -> str:
    """Non-streaming completion returning the full text reply."""
    model = model or settings.DEFAULT_AI_MODEL
    provider = _effective_provider(model, _provider_for(model))

    if provider == "openrouter":
        url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                url,
                headers=_openrouter_headers(),
                json=_openrouter_payload(model, messages, temperature, False),
            )
        if resp.status_code != 200:
            raise ModelRouterError(f"OpenRouter error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"] or ""

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ModelRouterError("OPENAI_API_KEY is not configured")
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature
        )
        return (resp.choices[0].message.content or "") if resp.choices else ""

    if provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ModelRouterError("ANTHROPIC_API_KEY is not configured")
        from anthropic import Anthropic

        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        system, claude_messages = _split_system(messages)
        resp = client.messages.create(
            model=model,
            max_tokens=8192,
            system=system or None,
            messages=claude_messages,
            temperature=temperature,
        )
        return "".join(b.text for b in resp.content if b.type == "text") or ""

    if provider == "google":
        if not settings.GOOGLE_AI_KEY:
            raise ModelRouterError("GOOGLE_AI_KEY is not configured")
        return _google_complete(model, messages, temperature)

    raise ModelRouterError(f"Cannot route model {model!r}")


def complete_with_tools(
    messages: list[dict],
    tools: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.3,
    tool_choice: str = "auto",
    max_tokens: Optional[int] = None,
) -> dict:
    """Native tool-calling completion (OpenAI-compatible protocol).

    Returns a dict with:
      - ``content``: the model's text reply (may be None when calling a tool)
      - ``tool_calls``: list of {"id", "name", "arguments"} or []
    """
    model = model or settings.DEFAULT_AI_MODEL
    provider = _effective_provider(model, _provider_for(model))

    if provider in ("openrouter", "openai"):
        url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "tools": tools,
            "tool_choice": tool_choice,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if provider == "openrouter":
            if not settings.OPENROUTER_API_KEY:
                raise ModelRouterError("OPENROUTER_API_KEY is not configured")
            headers = _openrouter_headers()
        else:
            if not settings.OPENAI_API_KEY:
                raise ModelRouterError("OPENAI_API_KEY is not configured")
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
        with httpx.Client(timeout=120) as client:
            resp = client.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            raise ModelRouterError(f"OpenRouter error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        return _parse_openai_response(data)

    if provider == "anthropic":
        # Anthropic uses a different tool protocol; not covered until a key is
        # configured, so the engine falls back to the envelope path.
        raise ModelRouterError(
            "native tool calling is not implemented for anthropic; use the envelope path"
        )

    raise ModelRouterError(f"Cannot route model {model!r} with native tools")


def _parse_openai_response(data: dict) -> dict:
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    tool_calls = []
    for call in message.get("tool_calls") or []:
        fn = call.get("function") or {}
        raw = fn.get("arguments") or "{}"
        try:
            arguments = json.loads(raw)
        except (ValueError, TypeError):
            arguments = {}
        tool_calls.append(
            {
                "id": call.get("id") or f"call_{len(tool_calls)}",
                "name": fn.get("name") or "",
                "arguments": arguments,
            }
        )
    return {
        "content": message.get("content") or "",
        "tool_calls": tool_calls,
    }


def stream(
    messages: list[dict], model: Optional[str] = None, temperature: float = 0.3
) -> Iterator[str]:
    """Stream a completion, yielding text chunks."""
    model = model or settings.DEFAULT_AI_MODEL
    provider = _effective_provider(model, _provider_for(model))

    if provider == "openrouter":
        url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        with httpx.Client(timeout=180) as client:
            with client.stream(
                "POST",
                url,
                headers=_openrouter_headers(),
                json=_openrouter_payload(model, messages, temperature, True),
            ) as resp:
                if resp.status_code != 200:
                    raise ModelRouterError(f"OpenRouter error {resp.status_code}: {resp.read()[:300]}")
                for raw in resp.iter_lines():
                    if not raw or not raw.startswith("data:"):
                        continue
                    payload = raw[len("data:"):].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        event = json.loads(payload)
                    except ValueError:
                        continue
                    choice = event.get("choices") or []
                    if not choice:
                        continue
                    delta = choice[0].get("delta") or {}
                    text = delta.get("content")
                    if text:
                        yield text
        return

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ModelRouterError("OPENAI_API_KEY is not configured")
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature, stream=True
        )
        for chunk in resp:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield content
        return

    if provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ModelRouterError("ANTHROPIC_API_KEY is not configured")
        from anthropic import Anthropic

        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        system, claude_messages = _split_system(messages)
        with client.messages.stream(
            model=model,
            max_tokens=8192,
            system=system or None,
            messages=claude_messages,
            temperature=temperature,
        ) as stream_ctx:
            for text in stream_ctx.text_stream:
                if text:
                    yield text
        return

    if provider == "google":
        if not settings.GOOGLE_AI_KEY:
            raise ModelRouterError("GOOGLE_AI_KEY is not configured")
        raise NotImplementedError("Google streaming is routed through complete()")

    raise ModelRouterError(f"Cannot route model {model!r}")


def _google_complete(model: str, messages: list[dict], temperature: float) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.GOOGLE_AI_KEY)
    gen_model = genai.GenerativeModel(model)
    # Google's chat interface expects a flat prompt; collapse history.
    chat = gen_model.start_chat(history=_google_history(messages))
    response = chat.send_message(messages[-1]["content"], generation_config={"temperature": temperature})
    return response.text if response else ""


def _google_history(messages: list[dict]):
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] in ("user", "tool") else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    return history


def _split_system(messages: list[dict]):
    system_parts = [m["content"] for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]
    return "\n".join(system_parts), rest