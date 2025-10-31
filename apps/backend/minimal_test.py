"""
Minimal FastAPI test - bypasses all custom code
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy", "test": "minimal"}

if __name__ == "__main__":
    print("=" * 60)
    print("MINIMAL TEST SERVER")
    print("http://localhost:8001")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
