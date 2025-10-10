# enginuity-backend/app/routers/quiz.py
from __future__ import annotations

import os
import re
import random
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from app.core.config import get_settings
from app.models.schemas import QuizRequest, QuizItem

router = APIRouter()

# ----------------------------
# OpenAI (optional)
# ----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
try:
    from openai import OpenAI  # type: ignore # openai>=1.0
    _openai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    _openai = None

# ----------------------------
# Config
# ----------------------------
MAX_CONTEXT_CHARS = 20000
MAX_ITEMS = 25
RANDOM_SEED = 17

STOPWORDS = set("""
a an and are as at be by for from has have if in into is it its of on or that the this to was were will with your you we i
""".split())

CONTACT_PATTERNS = [
    r"^dear\b.*",                      # greetings
    r"^hi\b.*",
    r"^hello\b.*",
    r"^best\b.*",                      # signatures
    r"^regards\b.*",
    r"^sincerely\b.*",
    r"\bbest regards\b",
    r"\bthanks\b",
    r"\bthank you\b",
    r"\bphone\b",
    r"\bemail\b",
    r"\blinked?in\b",
    r"\bgithub\b",
    r"\bportfolio\b",
    r"\bresume\b",
    r"\bcover letter\b",
    r"\bhiring\b.*team\b",
    r"\bcontact\b",
    r"\baddress\b",
    r"\+\d{1,3}\s?\d",                 # intl phone
    r"\(\d{3}\)\s?\d{3}-\d{4}",        # (999) 999-9999
    r"\d{3}-\d{3}-\d{4}",              # 999-999-9999
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",  # email
    r"https?://\S+",
]

# ---- Answer length / shaping ----
MIN_ANS_CHARS = 2
MAX_ANS_CHARS = 90          # keep MCQ answers succinct
MAX_ANS_TOKENS = 10         # ~1–10 words preferred for MCQ answers


# ----------------------------
# Utilities
# ----------------------------
def _clean_whitespace(s: str) -> str:
    s = (s or "").replace("\r", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _word_count(s: str) -> int:
    return len([w for w in re.findall(r"\b\w+\b", s or "")])

def _clip_clause(s: str) -> str:
    """
    Trim long clauses: cut at the first strong punctuation, prefer the left segment.
    """
    s = _clean_whitespace(s)
    for sep in [". ", "; ", ": ", " — ", " - "]:
        if sep in s:
            return s.split(sep, 1)[0]
    return s

def _shorten_for_mcq(s: str) -> str:
    """
    Prefer a short noun-phrase answer: clip long sentences and enforce token/char limits.
    """
    s = _clip_clause(s)
    if _word_count(s) > MAX_ANS_TOKENS:
        s = " ".join(s.split()[:MAX_ANS_TOKENS])
    return s[:MAX_ANS_CHARS].strip()

def _valid_answer_text(s: str) -> bool:
    s = _clean_whitespace(s)
    if not (MIN_ANS_CHARS <= len(s) <= MAX_ANS_CHARS):
        return False
    if _word_count(s) > MAX_ANS_TOKENS:
        return False
    alpha = sum(ch.isalpha() for ch in s)
    return (alpha / max(1, len(s))) >= 0.45

def _alpha_ratio(s: str) -> float:
    if not s:
        return 0.0
    alpha = sum(ch.isalpha() for ch in s)
    return alpha / max(1, len(s))

def _looks_like_contact_or_greeting(s: str) -> bool:
    low = s.strip().lower()
    for pat in CONTACT_PATTERNS:
        if re.search(pat, low):
            return True
    return False

def _meaningful_token(t: str) -> bool:
    t = t.strip().lower()
    return (
        len(t) >= 4
        and t not in STOPWORDS
        and bool(re.match(r"^[a-z][a-z0-9_\-]*$", t))
    )

def preprocess_context(raw: str) -> str:
    """
    Remove greetings/signatures/contact lines/URLs/emails, tiny lines, and low-alpha lines.
    Keep math/code blocks; keep sentences >= 15 chars or with key punctuation.
    """
    raw = _clean_whitespace(raw)
    lines = [ln.strip() for ln in raw.split("\n")]

    filtered: List[str] = []
    for ln in lines:
        if not ln:
            continue
        # Filter non-study lines
        if _looks_like_contact_or_greeting(ln):
            continue
        if len(ln) < 15 and not any(x in ln for x in (":", "=", "->", "∴", "∵")):
            continue
        if _alpha_ratio(ln) < 0.5 and not any(x in ln for x in ("=", "$", "\\", "∑", "∫", "→", "↦")):
            continue
        filtered.append(ln)

    # Merge and cap
    text = "\n".join(filtered).strip()
    if len(text) > MAX_CONTEXT_CHARS:
        text = text[:MAX_CONTEXT_CHARS]
    return text

def _difficulty_hint(diff: str) -> str:
    return {
        "auto": "balanced difficulty",
        "easy": "easier, factual recall",
        "medium": "moderate reasoning",
        "hard": "deeper multi-step reasoning",
    }.get((diff or "auto").lower(), "balanced difficulty")


# ----------------------------
# LLM generator (if configured)
# ----------------------------
SYSTEM_PROMPT = """You generate rigorous, unambiguous quiz questions strictly from the provided context.

Content policy:
- USE ONLY the provided context. Do NOT invent facts.
- IGNORE greetings, signatures, phone/email/links, and fluff.

MCQ rules:
- EXACTLY 4 options, one correct.
- The CORRECT ANSWER must be a SHORT noun phrase or term (≈1–8 words, <= 90 chars).
- Distractors must be plausible, distinct, and not trivial variations of the answer.
- The options must not overlap heavily or include “All of the above” / “None of the above”.

FIB rules:
- Blank out a KEY TERM or VALUE that appears in the context (not stopwords/punctuation).
- Keep stems clear and minimal.

General:
- Prefer concept-definition, property, classification, or relationship questions.
- Avoid yes/no, subjective, or trivial “What is X?” unless X is a defined technical term.
- Provide a 1-sentence explanation grounded in the context.

Return JSON ONLY as a list:
[
  { "q": "...", "choices": ["...","...","...","..."], "answer": "...", "explanation": "..." },
  ...
]
For FIB items, omit the "choices" field.
"""

def llm_generate(context: str, n: int, qtype: str, difficulty: str) -> List[QuizItem]:
    if not _openai:
        return []

    type_hint = {
        "mcq": "Generate only MCQs with short, noun-phrase answers (1–8 words).",
        "fib": "Generate only FIB; the blanked term is 1–3 words.",
        "mix": "Generate ~60% MCQ (short noun-phrase answers) and ~40% FIB.",
    }.get((qtype or "mcq").lower(), "Generate only MCQs with short, noun-phrase answers (1–8 words).")

    user_prompt = (
        f"Difficulty: {_difficulty_hint(difficulty)}.\n"
        f"{type_hint}\n"
        f"Number of questions: {min(max(1, n), MAX_ITEMS)}.\n"
        "Study material:\n"
        f"{context[:6000]}\n"
    )

    try:
        resp = _openai.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(content)
        items = parsed if isinstance(parsed, list) else parsed.get("items", [])
    except Exception:
        return []

    out: List[QuizItem] = []
    for it in items[:n]:
        q = _clean_whitespace(it.get("q", ""))
        raw_ans = _clean_whitespace(it.get("answer", ""))
        if not q or not raw_ans or len(q) < 8:
            continue

        choices = it.get("choices")
        expl = _clean_whitespace(it.get("explanation", "")) if it.get("explanation") else None

        if choices and isinstance(choices, list) and len(choices) >= 2:
            ans = _shorten_for_mcq(raw_ans)
            if not _valid_answer_text(ans):
                continue
            # shorten each choice and filter empties/dupes
            choice_short: List[str] = []
            seen = set()
            for c in choices[:4]:
                c2 = _shorten_for_mcq(_clean_whitespace(str(c)))
                if not c2 or c2 in seen:
                    continue
                choice_short.append(c2)
                seen.add(c2)
            # ensure answer is included
            if ans not in choice_short:
                choice_short = [ans] + [c for c in choice_short if c != ans]
            # need exactly 4: pad from remaining choices if available
            while len(choice_short) < 4 and len(choices) > len(choice_short):
                for c in choices:
                    c2 = _shorten_for_mcq(_clean_whitespace(str(c)))
                    if c2 and c2 not in choice_short and c2 != ans:
                        choice_short.append(c2)
                    if len(choice_short) == 4:
                        break
            if len(choice_short) != 4:
                continue
            random.shuffle(choice_short)
            out.append(QuizItem(q=q, choices=choice_short, answer=ans, explanation=expl))
        else:
            # FIB
            ans = raw_ans.strip()
            if not (MIN_ANS_CHARS <= len(ans) <= 64):
                continue
            out.append(QuizItem(q=q, answer=ans, explanation=expl))
    return out


# ----------------------------
# Deterministic fallback (grounded)
# ----------------------------
TECH_FALLBACKS = [
    "PostgreSQL","MySQL","SQLite","MongoDB","Redis","LangChain",
    "Transformers","NumPy","Pandas","React","Vue","Svelte",
    "Next.js","Django","FastAPI","PyTorch","TensorFlow"
]

def _key_lines(context: str) -> List[str]:
    lines = [ln.strip() for ln in context.split("\n") if ln.strip()]
    # prefer definitional/mathy lines
    keyish = [ln for ln in lines if (":" in ln or "=" in ln or r"\(" in ln or r"\math" in ln)]
    if not keyish:
        # aim for medium-length factual sentences
        keyish = [ln for ln in lines if 40 <= len(ln) <= 180 and not _looks_like_contact_or_greeting(ln)]
    return keyish[:300]

def _choose_term(line: str) -> Optional[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{3,}", line)
    for t in tokens:
        if _meaningful_token(t):
            return t
    return tokens[0] if tokens else None

def _make_fib(line: str) -> Optional[QuizItem]:
    term = _choose_term(line)
    if not term:
        return None
    if not _meaningful_token(term):
        return None
    q = line.replace(term, "____", 1)
    if len(q) < 20:
        return None
    return QuizItem(q=q, answer=term, explanation="Derived from the provided material.")

def _make_mcq(line: str, vocab: List[str]) -> Optional[QuizItem]:
    if ":" in line:
        concept, rhs = line.split(":", 1)
        stem = f"Which best describes {concept.strip()}?"
        ans = _shorten_for_mcq(rhs)
    elif "=" in line:
        lhs, rhs = line.split("=", 1)
        stem = f"In {lhs.strip()} = ?, what completes the relation?"
        ans = _shorten_for_mcq(rhs)
    else:
        term = _choose_term(line)
        if not term:
            return None
        stem = f"Which option best matches “{term}” in this context?"
        ans = _shorten_for_mcq(line)

    if not _valid_answer_text(ans):
        return None

    # Build plausible short distractors
    pool = [w for w in vocab if w and w.lower() not in ans.lower()]
    if len(pool) < 3:
        pool += [w for w in TECH_FALLBACKS if w.lower() not in ans.lower()]

    distractors: List[str] = []
    for w in pool:
        if not _meaningful_token(w):
            continue
        if len(w) > 30:
            continue
        distractors.append(w)
        if len(distractors) == 3:
            break
    if len(distractors) < 3:
        return None

    choices = [ans] + distractors
    random.shuffle(choices)
    return QuizItem(q=stem, choices=choices, answer=ans, explanation="Derived from the provided material.")

def rule_based_generate(context: str, n: int, qtype: str) -> List[QuizItem]:
    random.seed(RANDOM_SEED)
    lines = _key_lines(context)
    # vocabulary pool for distractors
    vocab = []
    for w in re.findall(r"[A-Za-z][A-Za-z0-9_\-]{3,}", context):
        if _meaningful_token(w):
            vocab.append(w)
    vocab = list(dict.fromkeys(vocab))[:400]
    items: List[QuizItem] = []

    def want_mcq(idx: int) -> bool:
        if qtype == "mcq":
            return True
        if qtype == "fib":
            return False
        return (idx % 5) not in {1, 4}  # ~60% MCQ

    i = 0
    for ln in lines:
        if i >= n:
            break
        it = _make_mcq(ln, vocab) if want_mcq(i) else _make_fib(ln)
        if it and it.q and it.answer and (len(it.q) >= 12):
            items.append(it)
            i += 1

    # Fill remaining with opposite type if needed
    j = 0
    while len(items) < n and j < len(lines):
        ln = lines[j]
        it = _make_fib(ln) if want_mcq(len(items)) else _make_mcq(ln, vocab)
        if it and it.q and it.answer and (len(it.q) >= 12):
            items.append(it)
        j += 1
    return items[:n]


# ----------------------------
# Build context from request (resilient)
# ----------------------------
def _load_notes_text_from_disk() -> str:
    """Concatenate section contents from DATA_DIR/notes.json for fallback."""
    try:
        settings = get_settings()
        notes_path = Path(settings.DATA_DIR).joinpath("notes.json").resolve()
        if notes_path.exists():
            doc = json.loads(notes_path.read_text(encoding="utf-8"))
            sections = doc.get("sections", []) or []
            parts: List[str] = []
            for s in sections:
                title = s.get("title", "")
                content = s.get("content", "")
                if not content:
                    continue
                if s.get("type") == "code":
                    parts.append(f"{title}\nCode:\n{content}\n")
                elif s.get("type") == "latex":
                    parts.append(f"{title}\nMath:\n{content}\n")
                else:
                    parts.append(f"{title}\n{content}\n")
            return "\n\n".join(parts).strip()
    except Exception:
        pass
    return ""

def build_context(req: QuizRequest) -> str:
    parts: List[str] = []

    # 1) UI-provided trimmed context (preferred)
    context_val = getattr(req, "context", None)
    if context_val:
        parts.append(str(context_val))

    # 2) Fallback: local notes.json if available
    if not parts:
        disk_text = _load_notes_text_from_disk()
        if disk_text:
            parts.append(disk_text)

    # 3) Last resort: topic (still filtered)
    if not parts and getattr(req, "topic", None):
        parts.append(str(req.topic))

    if not parts:
        raise HTTPException(
            status_code=400,
            detail="No study material found. Pass 'context' in the request or ensure data/notes.json exists (optionally provide 'topic')."
        )

    raw = "\n\n".join(parts)
    text = preprocess_context(raw)
    return text


# ----------------------------
# Endpoint (handle /quiz and /quiz/)
# ----------------------------
@router.post("", response_model=List[QuizItem])   # POST /quiz
@router.post("/", response_model=List[QuizItem])  # POST /quiz/
def gen_quiz(req: QuizRequest) -> List[QuizItem]:
    # Debug — appears in backend console
    try:
        print("QUIZ DEBUG:", {
            "using_openai": bool(_openai),
            "has_context": bool(getattr(req, "context", None)),
            "topic": getattr(req, "topic", None),
        })
    except Exception:
        pass

    n = max(1, min(int(req.n), MAX_ITEMS))
    qtype = (req.type or "mcq").lower().strip()
    if qtype in ("fill-in-the-blank", "fill in the blank", "fill_in_the_blank"):
        qtype = "fib"
    if qtype not in {"mcq", "fib", "mix"}:
        qtype = "mcq"

    difficulty = (req.difficulty or "auto").lower().strip()
    if difficulty not in {"auto", "easy", "medium", "hard"}:
        difficulty = "auto"

    context = build_context(req)  # filtered, capped

    try:
        print("QUIZ DEBUG 2:", {"pre_len": len(context)})
    except Exception:
        pass

    # Try LLM first (if configured)
    items = llm_generate(context, n, qtype, difficulty) if _openai else []
    # Fallback to deterministic generator
    if not items:
        items = rule_based_generate(context, n, qtype)

    # Final normalization: ensure choices sane and answer included
    out: List[QuizItem] = []
    seen_q = set()
    for it in items:
        q = _clean_whitespace(it.q)
        a = _clean_whitespace(it.answer)
        if not q or not a or q in seen_q:
            continue
        if _looks_like_contact_or_greeting(q.lower()):
            continue
        if len(q) < 12:
            continue

        if it.choices:
            # shorten and dedupe choices, ensure answer present
            ch_raw = list(it.choices or [])
            ch_proc: List[str] = []
            seen = set()
            for c in ch_raw:
                c2 = _shorten_for_mcq(_clean_whitespace(str(c)))
                if not c2 or c2 in seen:
                    continue
                ch_proc.append(c2)
                seen.add(c2)
            a_short = _shorten_for_mcq(a)
            if a_short not in ch_proc:
                ch_proc = [a_short] + [c for c in ch_proc if c != a_short]
            # ensure exactly 4
            if len(ch_proc) < 4:
                # pad with harmless tech fallbacks not equal to answer
                for w in TECH_FALLBACKS:
                    if w != a_short and w not in ch_proc:
                        ch_proc.append(w)
                    if len(ch_proc) == 4:
                        break
            if len(ch_proc) != 4 or not _valid_answer_text(a_short):
                continue
            random.shuffle(ch_proc)
            out.append(QuizItem(q=q, choices=ch_proc, answer=a_short, explanation=it.explanation))
        else:
            # FIB
            if "____" not in q:
                term_tokens = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{3,}", q)
                term = term_tokens[0] if term_tokens else a
                if term and term in q:
                    q = q.replace(term, "____", 1)
            if not (MIN_ANS_CHARS <= len(a) <= 64):
                continue
            out.append(QuizItem(q=q, answer=a, explanation=it.explanation))
        seen_q.add(q)

    if not out:
        raise HTTPException(status_code=422, detail="Could not generate quiz from the provided study material.")
    return out
