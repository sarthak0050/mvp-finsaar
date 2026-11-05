"""Retrieval over data/knowledge.md: Gemini embeddings + cosine, keyword-overlap fallback."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

import config

KB_PATH = Path(__file__).parent / "data" / "knowledge.md"
SIP_SOURCE = "Your SIP data"


@dataclass(frozen=True)
class Chunk:
    id: str
    title: str
    text: str
    keywords: tuple[str, ...]
    source: str

    @property
    def label(self) -> str:
        return f"{self.id} · {self.title}"


def parse_kb(md: str, amfi_link: str) -> list[Chunk]:
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    chunks = []
    for block in re.split(r"^## ", md, flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        cid, _, title = head.partition("·")
        text_lines, keywords, source = [], (), ""
        for line in body.strip().splitlines():
            if line.startswith("Keywords:"):
                keywords = tuple(k.strip().lower() for k in line[9:].split(",") if k.strip())
            elif line.startswith("Source:"):
                source = line[7:].strip().replace("{AMFI_LINK}", amfi_link)
            else:
                text_lines.append(line)
        chunks.append(Chunk(cid.strip(), title.strip(), "\n".join(text_lines).strip(), keywords, source))
    return chunks


@st.cache_resource(show_spinner=False)
def load_chunks() -> list[Chunk]:
    return parse_kb(KB_PATH.read_text(encoding="utf-8"), config.amfi_link())


# ---------- keyword fallback ----------

_STOP = set("a an the is are was of to in on for and or my me i it this that what why how does do kya ka ki ke hai se ko".split())


def _tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]+", s.lower()) if t not in _STOP and len(t) > 1}


def keyword_scores(question: str, chunks: list[Chunk]) -> list[float]:
    q = question.lower()
    qt = _tokens(q)
    scores = []
    for c in chunks:
        kw_hits = sum(2.0 for k in c.keywords if k in q)                 # phrase hits weigh more
        overlap = len(qt & _tokens(c.title + " " + c.text + " " + " ".join(c.keywords)))
        scores.append(kw_hits + overlap)
    return scores


# ---------- embeddings ----------

def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _embed(texts: list[str], task: str) -> list[list[float]]:
    from google.genai import types
    import llm
    client = llm.get_client()
    res = client.models.embed_content(
        model=config.EMBED_MODEL, contents=texts,
        config=types.EmbedContentConfig(task_type=task),
    )
    return [e.values for e in res.embeddings]


@st.cache_resource(show_spinner=False)
def chunk_embeddings() -> list[list[float]]:
    chunks = load_chunks()
    return _embed([f"{c.title}\n{c.text}\n{' '.join(c.keywords)}" for c in chunks], "RETRIEVAL_DOCUMENT")


@st.cache_data(show_spinner=False, max_entries=500)
def query_embedding(question: str) -> list[float]:
    return _embed([question], "RETRIEVAL_QUERY")[0]


def retrieve(question: str, k: int = 3) -> tuple[list[Chunk], str]:
    """Return top-k chunks and the method used ('embeddings' or 'keywords')."""
    chunks = load_chunks()
    method = "embeddings"
    try:
        q = query_embedding(question)
        # light keyword boost keeps Hinglish phrases ("doob gaya") on target
        kw = keyword_scores(question, chunks)
        scores = [_cos(q, e) + 0.02 * s for e, s in zip(chunk_embeddings(), kw)]
    except Exception:
        method = "keywords"
        scores = keyword_scores(question, chunks)
    order = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    return [chunks[i] for i in order[:k]], method
