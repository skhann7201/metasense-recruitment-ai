from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# For now, use simple imports - we'll add database later
app = FastAPI(title="MetaSense Recruitment API", version="1.0.0")

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "MetaSense Recruitment API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/test")
async def test_endpoint():
    return {"message": "Backend is working!"}