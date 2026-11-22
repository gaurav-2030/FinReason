"""One interface for local (Ollama) and API (OpenAI-compatible, Anthropic) chat models,
with token counting, latency measurement and an on-disk cache of every response."""
import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from dataclasses import dataclass

from .config import CACHE_DB, OLLAMA_URL, PRICES, SEED

# OpenAI-compatible providers: name -> (base URL, environment variable holding the API key)
OPENAI_COMPATIBLE = {
    "openai": (None, "OPENAI_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
}


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    latency: float          # seconds the model took (for cached answers: the original time)
    cached: bool = False


class ResponseCache:
    """SQLite key-value store: hash of the request -> JSON of the response."""

    def __init__(self, path=CACHE_DB):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False, timeout=30)
        self.db.execute("PRAGMA journal_mode=WAL")   # several programs can read and write at once
        self.db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT)")
        self.lock = threading.Lock()   # one connection shared by worker threads

    def get(self, key):
        try:
            with self.lock:
                row = self.db.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
        except sqlite3.OperationalError:   # database busy: treat it as a cache miss
            return None
        return json.loads(row[0]) if row else None

    def put(self, key, value):
        try:
            with self.lock:
                self.db.execute("INSERT OR REPLACE INTO cache VALUES (?, ?)", (key, json.dumps(value)))
                self.db.commit()
        except sqlite3.OperationalError:   # database busy: the answer is returned, just not cached
            pass


class LLM:
    """spec is 'provider:model', e.g. 'ollama:qwen3:8b', 'groq:llama-3.3-70b-versatile',
    'openai:gpt-4o-mini'."""

    def __init__(self, spec, think=False, max_tokens=1024, num_ctx=8192, use_cache=True):
        self.spec = spec
        self.provider, self.model = spec.split(":", 1)
        self.think = think
        self.max_tokens = max_tokens
        self.num_ctx = num_ctx
        self.cache = ResponseCache() if use_cache else None
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if self.provider == "ollama":
                import ollama
                self._client = ollama.Client(host=OLLAMA_URL)
            elif self.provider == "anthropic":
                import anthropic
                self._client = anthropic.Anthropic()
            elif self.provider in OPENAI_COMPATIBLE:
                from openai import OpenAI
                base_url, key_var = OPENAI_COMPATIBLE[self.provider]
                self._client = OpenAI(base_url=base_url, api_key=os.environ[key_var])
            else:
                raise ValueError(f"unknown provider {self.provider}")
        return self._client

    def chat(self, messages, temperature=0.0, sample_id=0):
        """Send a list of {'role', 'content'} messages and return an LLMResponse.
        sample_id distinguishes repeated samples of the same prompt (self-consistency)."""
        request = [self.spec, self.think, self.max_tokens, messages, temperature, sample_id]
        key = hashlib.sha256(json.dumps(request).encode()).hexdigest()
        if self.cache and (hit := self.cache.get(key)):
            return LLMResponse(**hit, cached=True)
        start = time.perf_counter()
        for attempt in range(3):
            try:
                text, n_in, n_out = self._call(messages, temperature, sample_id)
                if not text and n_in == 0 and n_out == 0:
                    # an empty reply that processed no tokens is a server failure (for example the GPU ran
                    # out of memory), not an answer: retry it and never cache it
                    raise RuntimeError(f"{self.spec} returned an empty response (server error)")
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt * 5)
        latency = time.perf_counter() - start
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        if self.cache:
            self.cache.put(key, {"text": text, "prompt_tokens": n_in,
                                 "completion_tokens": n_out, "latency": latency})
        return LLMResponse(text, n_in, n_out, latency)

    def _call(self, messages, temperature, sample_id):
        if self.provider == "ollama":
            options = {"temperature": temperature, "seed": SEED + sample_id,
                       "num_ctx": self.num_ctx, "num_predict": self.max_tokens}
            try:
                r = self.client.chat(model=self.model, messages=messages, think=self.think,
                                     keep_alive="30m", options=options)
            except Exception as exc:   # models without a thinking mode reject the think flag
                if "think" not in str(exc).lower():
                    raise
                r = self.client.chat(model=self.model, messages=messages, keep_alive="30m",
                                     options=options)
            return r.message.content, r.prompt_eval_count or 0, r.eval_count or 0
        if self.provider == "anthropic":
            system = "\n".join(m["content"] for m in messages if m["role"] == "system")
            rest = [m for m in messages if m["role"] != "system"]
            r = self.client.messages.create(model=self.model, system=system, messages=rest,
                                            max_tokens=self.max_tokens, temperature=temperature)
            return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens
        r = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=temperature,
            max_tokens=self.max_tokens, seed=SEED + sample_id,
        )
        return r.choices[0].message.content or "", r.usage.prompt_tokens, r.usage.completion_tokens


def cost_usd(spec, prompt_tokens, completion_tokens):
    """Dollar cost of a call for API models with a known price; 0 for local models."""
    price_in, price_out = PRICES.get(spec, (0.0, 0.0))
    return (prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000
