from fastapi import APIRouter
from app.models.schemas import QuizRequest, QuizItem
from typing import List

router = APIRouter()

BASE = [
    {"q": "What is the Laplace transform of 1?", "choices": ["1/s", "s", "0", "∞"], "answer": "1/s",
     "explanation": "𝓛{1} = ∫₀^∞ e^{-st} dt = 1/s for Re(s) > 0."},
    {"q": "Poles in the right half-plane imply ____", "choices": ["stability", "instability", "oscillation", "causality"], "answer": "instability",
     "explanation": "Right-half-plane poles (Re(s) > 0) → divergent modes → unstable."},
    {"q": "For causal LTI systems, the ROC of Laplace transform is:", "choices": ["Left of rightmost pole", "Right of rightmost pole", "A vertical line Re(s)=0", "Entire s-plane"], "answer": "Right of rightmost pole"},
    {"q": "Convolution in time corresponds to ____ in the Laplace domain.", "choices": ["Addition", "Subtraction", "Multiplication", "Division"], "answer": "Multiplication"},
    {"q": "The step response is the integral of the ____ response.", "choices": ["Impulse", "Frequency", "Ramp", "Sinusoidal"], "answer": "Impulse"},
    {"q": "A BIBO stable system has impulse response h(t) that is:", "choices": ["Square-integrable", "Absolutely integrable", "Differentiable", "Periodic"], "answer": "Absolutely integrable"},
]

@router.post("", response_model=List[QuizItem])
def gen_quiz(req: QuizRequest):
    n = max(1, min(req.n, len(BASE)))
    items = [QuizItem(**it) for it in BASE[:n]]
    if req.type.lower() in ("fill-in-the-blank", "fib", "mix"):
        # convert every 3rd question to FIB for 'mix', or all for 'fib'
        fib_all = req.type.lower() in ("fill-in-the-blank", "fib")
        out = []
        for i, it in enumerate(items, 1):
            if fib_all or (i % 3 == 0):
                out.append(QuizItem(q=it.q.replace(it.answer, "____") if it.answer in it.q else f"{it.q}  (Answer: ____)", choices=[], answer=it.answer, explanation=it.explanation))
            else:
                out.append(it)
        items = out
    return items
