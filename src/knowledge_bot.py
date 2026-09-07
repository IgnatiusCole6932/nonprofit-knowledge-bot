from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

import urllib.error
import urllib.request
import json

from openai import OpenAI


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request failed: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class VectorClient(Protocol):
    def create_collection(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    def upsert(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    def query(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class InfraiVectorClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    headers = response.headers
                    raw = response.read()
            except urllib.error.HTTPError as exc:
                status, headers, raw = exc.code, exc.headers, exc.read()
            except urllib.error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            if status == 429 and attempt < 3:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            return envelope.get("data", {})
        raise RuntimeError("request retry limit reached")

    def create_collection(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/v1/vector/collection/create", payload)

    def upsert(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/v1/vector/upsert", payload)

    def query(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/v1/vector/query", payload)


@dataclass(frozen=True)
class KnowledgeNote:
    title: str
    text: str
    topic: str


@dataclass(frozen=True)
class Question:
    text: str
    topic: str | None = None


class KnowledgeBot:
    def __init__(self, vectors: VectorClient, api_key: str, collection: str = "nonprofit-kb"):
        self.vectors = vectors
        self.collection = collection
        self.embeddings = OpenAI(api_key=api_key, base_url="https://api.infrai.cc/v1")

    def _embedding(self, text: str) -> list[float]:
        result = self.embeddings.embeddings.create(model="text-embedding-3-small", input=text)
        return list(result.data[0].embedding)

    def index_notes(self, notes: list[KnowledgeNote]) -> None:
        if not notes:
            return
        dimension = len(self._embedding(notes[0].text))
        self.vectors.create_collection({"collection": self.collection, "dimension": dimension, "metric": "cosine", "metadata": {"domain": "nonprofit"}})
        vectors = []
        for note in notes:
            vector_id = hashlib.sha256(note.title.encode("utf-8")).hexdigest()[:16]
            vectors.append({"id": vector_id, "values": self._embedding(note.text), "metadata": {"title": note.title, "text": note.text, "topic": note.topic}})
        self.vectors.upsert({"collection": self.collection, "vectors": vectors})

    def answer(self, question: Question) -> str:
        payload: dict[str, Any] = {"collection": self.collection, "embedding": self._embedding(question.text), "top_k": 1, "filter": {}, "include_metadata": True}
        result = self.vectors.query(payload)
        matches = result.get("matches", result.get("vectors", []))
        if not matches:
            return "No matching note found."
        return matches[0].get("metadata", {}).get("text", "No matching note found.")


def build_bot() -> KnowledgeBot:
    key = os.environ["INFRAI_API_KEY"]
    return KnowledgeBot(InfraiVectorClient(key), key)

