import os
import re
import uuid
from datetime import datetime
from typing import Any

import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Simple backend with correct MyHibachi FAQ data
app = FastAPI(title="MyHibachi AI Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    page: str
    consent_to_save: bool | None = False
    city: str | None = None


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    route: str
    sources: list[dict[str, Any]] = []
    can_escalate: bool = True
    log_id: str | None = None


class FeedbackRequest(BaseModel):
    log_id: str
    feedback: str
    suggestion: str | None = None


# CORRECTED FAQ data based on actual MyHibachi service
FAQ_DATA = [
    {
        "id": "1",
        "question": "What's included in the hibachi service?",
        "answer": "Our hibachi service includes a professional chef, portable hibachi grill, all cooking equipment, and utensils. We provide hibachi vegetables (zucchini, onions, mushrooms), fried rice, and your choice of proteins. Please note: We do NOT include cleanup service, tables, chairs, or dinnerware - these need to be arranged separately.",  # noqa: E501
        "category": "service",
        "keywords": [
            "included",
            "service",
            "what comes with",
            "hibachi service",
            "equipment",
            "cleanup",
            "tables",
            "chairs",
        ],
    },
    {
        "id": "2",
        "question": "Do you serve Sacramento?",
        "answer": "Yes! We serve anywhere in Northern California including the greater Sacramento area (Roseville, Folsom, Davis, and surrounding cities). We have reasonable travel fees that apply based on distance from our base location.",  # noqa: E501
        "category": "service_area",
        "keywords": [
            "sacramento",
            "serve",
            "area",
            "travel",
            "northern california",
            "roseville",
            "folsom",
            "davis",
        ],
    },
    {
        "id": "3",
        "question": "How much is the deposit?",
        "answer": "We require a $100 refundable deposit to secure your booking. This deposit is refundable according to our terms and conditions (please check the agreement section). The remaining balance is due on the event day.",  # noqa: E501
        "category": "pricing",
        "keywords": [
            "deposit",
            "cost",
            "price",
            "refundable",
            "100",
            "hundred",
            "booking",
            "terms",
            "conditions",
        ],
    },
    {
        "id": "4",
        "question": "What proteins do you offer?",
        "answer": "We offer premium proteins including chicken, beef steak, shrimp, salmon, tofu for vegetarians, and combination options. All proteins are fresh and prepared with our signature hibachi seasonings.",  # noqa: E501
        "category": "menu",
        "keywords": [
            "proteins",
            "chicken",
            "beef",
            "steak",
            "shrimp",
            "salmon",
            "tofu",
            "vegetarian",
            "meat",
            "options",
        ],
    },
    {
        "id": "5",
        "question": "Where do you serve? What's your service area?",
        "answer": "We serve throughout Northern California including the Bay Area (San Francisco, San Jose, Oakland, Palo Alto, Mountain View, Santa Clara, Sunnyvale, Fremont) and the greater Sacramento area. We charge reasonable travel fees based on distance from our base location.",  # noqa: E501
        "category": "service_area",
        "keywords": [
            "service area",
            "bay area",
            "san francisco",
            "san jose",
            "oakland",
            "palo alto",
            "mountain view",
            "santa clara",
            "sunnyvale",
            "fremont",
            "travel fee",
        ],
    },
    {
        "id": "6",
        "question": "What's your cancellation policy?",
        "answer": "Please refer to our terms and conditions in the agreement section for our complete cancellation policy. The $100 deposit refund is subject to these terms and conditions.",  # noqa: E501
        "category": "policy",
        "keywords": [
            "cancellation",
            "policy",
            "refund",
            "terms",
            "conditions",
            "agreement",
        ],
    },
    {
        "id": "7",
        "question": "Do you provide cleanup service?",
        "answer": "No, we do not provide cleanup service. Our service includes the chef, equipment, cooking, and food preparation. Cleanup, tables, chairs, and dinnerware are not included and need to be arranged separately by the customer.",  # noqa: E501
        "category": "service",
        "keywords": [
            "cleanup",
            "clean",
            "tables",
            "chairs",
            "dinnerware",
            "not included",
        ],
    },
    {
        "id": "8",
        "question": "What about tables and chairs?",
        "answer": "Tables, chairs, and dinnerware are not included in our hibachi service. These need to be arranged separately by the customer. We focus on providing the chef, cooking equipment, and delicious hibachi food.",  # noqa: E501
        "category": "service",
        "keywords": [
            "tables",
            "chairs",
            "dinnerware",
            "not included",
            "arrange separately",
        ],
    },
]


# Simple PII scrubber
def scrub_pii(text: str) -> str:
    # Email pattern
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", text
    )
    # Phone pattern
    text = re.sub(
        r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?"
        r"([0-9]{3})[-.\s]?([0-9]{4})\b",
        "[PHONE]",
        text,
    )
    # SSN pattern
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]", text)
    return text


# Enhanced FAQ search with keyword matching
def search_faqs(query: str, limit: int = 3) -> list[dict[str, Any]]:
    query_lower = query.lower()
    scores = []

    for faq in FAQ_DATA:
        question_score = 0
        answer_score = 0
        keyword_score = 0

        # Direct question matching (highest weight)
        if (
            query_lower in faq["question"].lower()
            or faq["question"].lower() in query_lower
        ):
            question_score += 10

        # Keyword matching
        for keyword in faq["keywords"]:
            if keyword.lower() in query_lower:
                keyword_score += 3

        # Word-by-word matching - only keep variables that are used
        query_words = query_lower.split()

        for word in query_words:
            if len(word) > 2:  # Skip very short words
                if word in faq["question"].lower():
                    question_score += 2
                if word in faq["answer"].lower():
                    answer_score += 1

        total_score = question_score + answer_score + keyword_score
        if total_score > 0:
            scores.append(
                {
                    "faq_id": faq["id"],
                    "question": faq["question"],
                    "answer": faq["answer"],
                    "score": total_score / max(len(query_words), 1),
                    "category": faq["category"],
                }
            )

    # Sort by score and return top results
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:limit]


# OpenAI fallback with MyHibachi context
async def call_openai(message: str, context: str = "") -> tuple[str, float]:
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        system_prompt = f"""You are a helpful assistant for MyHibachi, a
premium hibachi catering service in Northern California.

IMPORTANT SERVICE DETAILS:
- We serve throughout Northern California (Bay Area, Sacramento area)
- Deposit: $100 refundable (subject to terms and conditions)
- We DO NOT provide cleanup service, tables, chairs, or dinnerware
- We DO provide: chef, portable grill, equipment, utensils, vegetables,
fried rice, proteins
- Travel fees apply based on distance
- Service areas: San Francisco, San Jose, Oakland, Sacramento, Palo Alto,
Mountain View, Santa Clara, Sunnyvale, Fremont, and surrounding areas

Context from our FAQs: {context}

Guidelines:
- Be friendly and professional
- Use the EXACT information provided above
- If asked about booking, direct to contact information
- Keep responses concise but informative
- If unsure about specific details, suggest contacting the team directly
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            max_tokens=200,
            temperature=0.7,
        )

        return response.choices[0].message.content, 0.8

    except Exception as e:
        print(f"OpenAI error: {e}")
        return (
            "I'm having trouble accessing my knowledge right now. Please contact our team directly for assistance.",  # noqa: E501
            0.2,
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Scrub PII from message
        clean_message = scrub_pii(request.message)

        # Search FAQs first
        faq_results = search_faqs(clean_message)

        if (
            faq_results and faq_results[0]["score"] > 2.0
        ):  # Increased threshold for better matching
            # High confidence FAQ match
            best_faq = faq_results[0]
            return ChatResponse(
                answer=best_faq["answer"],
                confidence=min(
                    best_faq["score"] / 10.0, 0.95
                ),  # More realistic confidence scoring
                route="local",
                sources=[
                    {
                        "faq_id": best_faq["faq_id"],
                        "score": best_faq["score"],
                        "question": best_faq["question"],
                    }
                ],
                log_id=str(uuid.uuid4()),
            )

        # Fallback to OpenAI with context
        context = ""
        if faq_results:
            # Fix f-string nesting for Python 3.11 compatibility
            faq_summaries = []
            for r in faq_results[:2]:
                summary = f"{r['question']}: {r['answer'][:100]}..."
                faq_summaries.append(summary)
            context = f"Related FAQs: {'; '.join(faq_summaries)}"

        answer, confidence = await call_openai(clean_message, context)

        return ChatResponse(
            answer=answer,
            confidence=confidence,
            route="openai",
            sources=[],
            log_id=str(uuid.uuid4()),
        )

    except Exception as e:
        print(f"Chat error: {e}")
        return ChatResponse(
            answer="I'm experiencing technical difficulties. Please contact "
            "our team directly for immediate assistance.",
            confidence=0.1,
            route="error",
            sources=[],
            log_id=str(uuid.uuid4()),
        )


@app.post("/api/v1/feedback")
async def submit_feedback(request: FeedbackRequest):
    try:
        # For now, just log the feedback
        print(f"Feedback received: {request.log_id} -> {request.feedback}")
        if request.suggestion:
            print(f"Suggestion: {request.suggestion}")

        return {"status": "success", "message": "Feedback recorded"}

    except Exception as e:
        print(f"Feedback error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process feedback"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
