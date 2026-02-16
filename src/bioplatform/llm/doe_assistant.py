from __future__ import annotations

import json
import os
from dataclasses import dataclass
from itertools import product
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

Provider = Literal["chatgpt", "gemini"]


@dataclass(slots=True)
class DoEMessage:
    role: Literal["user", "assistant"]
    content: str


class DoEAssistant:
    """Design-of-experiments assistant with ChatGPT/Gemini backends.

    This class keeps a local message history and can either:
    - call ChatGPT API (`provider='chatgpt'` with OPENAI_API_KEY), or
    - call Gemini API (`provider='gemini'` with GEMINI_API_KEY).
    """

    def __init__(self, provider: Provider = "chatgpt", api_key: str | None = None) -> None:
        self.provider = provider
        self.api_key = api_key or self._read_key(provider)
        self.history: list[DoEMessage] = []

    @staticmethod
    def _read_key(provider: Provider) -> str | None:
        if provider == "chatgpt":
            return os.environ.get("OPENAI_API_KEY")
        return os.environ.get("GEMINI_API_KEY")

    @staticmethod
    def system_prompt() -> str:
        return (
            "You are an experimental design assistant for biology labs. "
            "Recommend statistically sound, practical designs with sample-size and randomization guidance."
        )

    def chat(self, user_message: str) -> str:
        self.history.append(DoEMessage("user", user_message))
        if not self.api_key:
            return (
                "API key missing. Configure OPENAI_API_KEY for ChatGPT or GEMINI_API_KEY for Gemini."
            )

        if self.provider == "chatgpt":
            return self._chatgpt_chat(user_message)
        return self._gemini_chat(user_message)

    def _chatgpt_chat(self, user_message: str) -> str:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": self.system_prompt()},
                *[{"role": m.role, "content": m.content} for m in self.history],
            ],
            "temperature": 0.2,
        }
        req = Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=40) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            message = body["choices"][0]["message"]["content"]
            self.history.append(DoEMessage("assistant", message))
            return message
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            return f"ChatGPT request failed: {exc}"

    def _gemini_chat(self, user_message: str) -> str:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={self.api_key}"
        )
        prompt = self.system_prompt() + "\n\n" + "\n".join(f"{m.role}: {m.content}" for m in self.history)
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        req = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=40) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            message = body["candidates"][0]["content"]["parts"][0]["text"]
            self.history.append(DoEMessage("assistant", message))
            return message
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            return f"Gemini request failed: {exc}"

    def generate_factorial_design(self, factors: list[str], levels: list[int]) -> list[dict[str, int]]:
        if len(factors) != len(levels):
            raise ValueError("factors and levels must have same length")
        runs = product(*[range(level) for level in levels])
        return [dict(zip(factors, run)) for run in runs]

    def reset_conversation(self) -> None:
        self.history.clear()
