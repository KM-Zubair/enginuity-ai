from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()

@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Placeholder — echoes a domain-specific tip
    demo_text = (
        "Stability requires all poles to lie in the left half-plane. "
        "For a step input, examine the dominant pole to estimate settling time."
    )
    demo_citations = [
        {"title": "Poles & stability", "section_id": "sec-1", "score": 0.78, "snippet": "A linear system is stable if all poles lie strictly in the left half-plane."},
        {"title": "Laplace Transform — definition", "section_id": "sec-2", "score": 0.73, "snippet": "𝓛{f(t)} = ∫₀^∞ f(t)e^{-st} dt."},
    ]
    return ChatResponse(text=demo_text, citations=demo_citations)
