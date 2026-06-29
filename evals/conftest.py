"""
pytest fixtures for the Cardinal Court eval suite.
Provides a lightweight call() fixture that sends a question to the LLM
with the full system prompt — text-only, no voice round-trip.
"""
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))

from knowledge import build_system_prompt  # noqa: E402

SYSTEM_PROMPT = build_system_prompt()


@pytest.fixture(scope="session")
def ask():
    """Return a function that sends a question to gpt-4.1-mini with the KB system prompt."""
    from openai import OpenAI  # type: ignore

    client = OpenAI()

    def _ask(question: str) -> str:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            max_tokens=200,
            temperature=0,
        )
        return (resp.choices[0].message.content or "").lower()

    return _ask
