"""
Minimal AI API test
"""

from fastapi import FastAPI

app = FastAPI(
    title="MyHibachi AI API",
    description="Dedicated AI service for chat, learning, and content generation",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "myhibachi-ai-api"}


@app.get("/")
async def root():
    return {"message": "MyHibachi AI API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main_simple:app", host="0.0.0.0", port=8002, reload=True)
