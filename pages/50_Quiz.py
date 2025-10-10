# quiz.py
import sys
from pathlib import Path
import json
import random
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from ui.bootstrap import ensure_corpus

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from ui.theme import load_css
import httpx  # NEW

# IMPORTANT: set_page_config should be called only once in the main entry page.
# st.set_page_config(page_title="Quiz", page_icon="🧩", layout="wide")

load_css("base.css")

ready = ensure_corpus()
if not ready:
    st.warning("No saved corpus found. Upload and process a lecture to generate quizzes.")
    try:
        st.page_link("pages/Upload.py", label="Go to Upload", icon="📤")
    except Exception:
        pass
    # You may continue; the page can still use local notes.json as fallback
    # st.stop()

# prefer backend-provided meta when available
if st.session_state.get("lecture_title"):
    lecture_title = st.session_state["lecture_title"]
if st.session_state.get("generated_at"):
    try:
        ts = int(st.session_state["generated_at"])
        st.caption(
            f"Lecture: **{lecture_title}** · Generated: "
            f"{datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')}"
        )
    except Exception:
        pass

if not st.session_state.get("has_corpus"):
    st.warning("Upload and process a lecture to generate quizzes.")
    try:
        st.page_link("pages/Upload.py", label="Go to Upload", icon="📤")
    except Exception:
        pass
    st.stop()

st.markdown('<div class="quiz-page">', unsafe_allow_html=True)
st.title("Quiz")

DATA_DIR = Path("data")
NOTES_JSON = DATA_DIR / "notes.json"
lecture_title = "Notes"
if NOTES_JSON.exists():
    try:
        doc = json.loads(NOTES_JSON.read_text(encoding="utf-8"))
        lecture_title = doc.get("lecture_title", lecture_title)
        ts = doc.get("generated_at")
        if ts:
            st.caption(
                f"Lecture: **{lecture_title}** · Generated: "
                f"{datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')}"
            )
    except Exception:
        pass

# ---------- Helpers ----------
def reset_attempt_state() -> None:
    st.session_state["quiz_answers"] = {}      # question_idx -> user answer (string)
    st.session_state["quiz_submitted"] = False
    st.session_state["quiz_score"] = None

def shuffle_choices(choices: List[str], answer: str):
    """Return (shuffled_choices, correct_index) while preserving the correct answer string."""
    if not choices:
        return [], None
    items = list(choices)
    random.shuffle(items)
    correct_index = items.index(answer) if answer in items else None
    return items, correct_index

def load_local_sections() -> List[Dict[str, Any]]:
    """Read sections from notes.json (used to scope quiz generation)."""
    if NOTES_JSON.exists():
        try:
            _doc = json.loads(NOTES_JSON.read_text(encoding="utf-8"))
            secs = _doc.get("sections", [])
            # keep only blocks that have content
            return [s for s in secs if s.get("content")]
        except Exception:
            return []
    return []

# ---------- Section scope (optional) ----------
all_sections = load_local_sections()
section_titles = [s.get("title", "Untitled") for s in all_sections]

with st.expander("Section scope (optional)"):
    picked_titles = st.multiselect(
        "Only generate questions from these sections",
        options=section_titles,
        default=section_titles[:4] if section_titles else []
    )
    picked = [s for s in all_sections if s.get("title", "Untitled") in picked_titles]

# ---------- Controls ----------
with st.form("quiz_controls"):
    c1, c2, c3 = st.columns([1, 1, 2])
    n_questions = c1.slider("Number of questions", 3, 25, 6)
    qtype = c2.selectbox("Type", ["MCQ", "Fill-in-the-blank", "Mix"])
    difficulty = c3.selectbox("Difficulty", ["Auto", "Easy", "Medium", "Hard"])
    topic_seed = st.text_input("Optional topic focus", placeholder="e.g., Laplace, stability, convolution")
    generated = st.form_submit_button("Generate Quiz")

FASTAPI_URL = (os.getenv("FASTAPI_URL", "http://127.0.0.1:8000") or "").rstrip("/")

# ---------- Generate via backend ----------
if generated:
    # Build scoped context from selected sections (or all sections if none picked)
    section_ids: List[str] = [s.get("id", "") for s in picked] if picked else []
    raw_context_parts: List[str] = []
    for s in (picked or all_sections):
        title = s.get("title", "")
        content = s.get("content", "")
        s_type = s.get("type", "text")
        if not content:
            continue
        if s_type == "code":
            raw_context_parts.append(f"{title}\nCode:\n{content}\n")
        elif s_type == "latex":
            raw_context_parts.append(f"{title}\nMath:\n{content}\n")
        else:
            raw_context_parts.append(f"{title}\n{content}\n")

    context_text = "\n\n".join(raw_context_parts).strip()

    # cap payload size to keep requests snappy
    if len(context_text) > 12000:
        context_text = context_text[:12000]

    # Guard: don't submit if there is no study text
    if not context_text.strip() and not (topic_seed and topic_seed.strip()):
        st.error("No study material found. Select relevant sections or provide a topic focus.")
        st.stop()

    # Small debug badge so you know what's being sent
    st.caption(f"Context chars: {len(context_text)}")

    payload: Dict[str, Any] = {
        "n": int(n_questions),
        "type": str((qtype or "MCQ")).lower(),
        "difficulty": str((difficulty or "Auto")).lower(),
        "topic": topic_seed or None,
        "section_ids": section_ids or None,
        "context": context_text or None,    # backend prefers this
        "corpus_id": st.session_state.get("corpus_id"),
        "lecture_title": lecture_title,
    }

    # normalize qtype to what backend expects
    if payload["type"] in ("fill-in-the-blank", "fill in the blank", "fill_in_the_blank"):
        payload["type"] = "fib"

    try:
        with st.spinner("Generating quiz…"):
            # Accept both /quiz and /quiz/ (router supports both)
            r = httpx.post(f"{FASTAPI_URL}/quiz", json=payload, timeout=60.0)
            r.raise_for_status()
            items_from_api: List[Dict[str, Any]] = r.json() or []
    except Exception as e:
        st.error(f"Quiz generation failed: {e}")
        items_from_api = []

    # Prepare a view-model with shuffled choices (don’t mutate originals)
    vm: List[Dict[str, Any]] = []
    for it in items_from_api:
        choices = it.get("choices", [])
        if choices:
            shuf, _ = shuffle_choices(choices, it.get("answer", ""))
            vm.append({**it, "choices_shuf": shuf})
        else:
            vm.append({**it, "choices_shuf": []})

    st.session_state["quiz_items"] = vm
    st.session_state["quiz_meta"] = {
        "lecture": lecture_title,
        "n": len(vm),
        "type": qtype,
        "difficulty": difficulty,
        "topic": topic_seed,
        "generated_at": datetime.now().isoformat(),
        "section_ids": section_ids,
    }
    reset_attempt_state()

items = st.session_state.get("quiz_items", [])
meta = st.session_state.get("quiz_meta", {})

if not items:
    st.info("Set your preferences above and click **Generate Quiz**.")
else:
    # ---------- Render Quiz ----------
    st.subheader(f"{meta.get('lecture','Notes')} · {meta.get('type','MCQ')} · {meta.get('difficulty','Auto')}")
    focus = f" · Focus: {meta['topic']}" if meta.get("topic") else ""
    st.caption(f"{meta.get('n', len(items))} questions{focus}")
    if meta.get("section_ids"):
        st.caption(f"Scoped to {len(meta['section_ids'])} section(s)")

    # Render each item
    for i, item in enumerate(items, 1):
        st.markdown("<div class='quiz-card'>", unsafe_allow_html=True)
        st.write(f"**{i}.** {item.get('q', '')}")

        # MCQ
        if item.get("choices_shuf"):
            user = st.radio(
                "Choose:",
                options=item["choices_shuf"],
                key=f"ans-{i}",
                horizontal=True,
                index=None  # start with nothing selected
            )
            st.session_state["quiz_answers"][i] = user or ""
        else:
            # Fill-in-the-blank
            user = st.text_input("Your answer", key=f"ans-{i}")
            st.session_state["quiz_answers"][i] = (user or "").strip()

        st.markdown("</div>", unsafe_allow_html=True)

    # Actions (submit / download / reset)
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        submit = st.button("Submit All ✅")
    with c2:
        dl_payload = {"meta": meta, "items": items}
        st.download_button("Download .json", data=json.dumps(dl_payload, indent=2), file_name="quiz.json")
    with c3:
        if st.button("Retake / Regenerate 🔁"):
            # Keep the same parameters; reshuffle choices
            for it in items:
                if it.get("choices"):
                    shuf, _ = shuffle_choices(it["choices"], it["answer"])
                    it["choices_shuf"] = shuf
            reset_attempt_state()

    # ---------- Grade & Review ----------
    if submit and not st.session_state.get("quiz_submitted"):
        answers = st.session_state.get("quiz_answers", {})
        correct = 0
        review = []
        for i, it in enumerate(items, 1):
            gold = str(it.get("answer", ""))
            pred = str(answers.get(i, "") or "")
            is_mcq = bool(it.get("choices"))
            if is_mcq:
                ok = (pred == gold)
            else:
                ok = pred.strip().lower() == gold.strip().lower()
            correct += int(ok)
            review.append({
                "i": i,
                "q": it.get("q", ""),
                "your": pred or "—",
                "answer": gold,
                "ok": ok,
                "explanation": it.get("explanation", ""),
            })

        st.session_state["quiz_submitted"] = True
        st.session_state["quiz_score"] = {"correct": correct, "total": len(items), "review": review}

    # Show results if submitted
    if st.session_state.get("quiz_submitted"):
        sc = st.session_state["quiz_score"]
        pct = 100.0 * sc["correct"] / max(1, sc["total"])
        st.success(f"Score: **{sc['correct']} / {sc['total']}**  ({pct:.0f}%)")

        with st.expander("Review answers"):
            for r in sc["review"]:
                icon = "✅" if r["ok"] else "❌"
                st.markdown(f"**{r['i']}.** {icon} {r['q']}")
                st.caption(f"Your answer: {r['your'] or '—'}")
                if not r["ok"]:
                    st.write(f"**Correct:** {r['answer']}")
                if r.get("explanation"):
                    st.info(r["explanation"])

# ---------- Notes ----------
# Backend contract: POST /quiz
# Request: {
#   n, type: "mcq"|"fib"|"mix", difficulty, topic?,
#   section_ids?: string[], context?: string, corpus_id?: string, lecture_title?: string
# }
# Response: [ { q, choices?:[], answer, explanation? }, ... ]

st.markdown('</div>', unsafe_allow_html=True)
