"""
Main FastAPI application for SmartApply Human-in-the-Loop.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.human_endpoints import router as human_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smartapply_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SmartApply API",
    description="Human-in-the-Loop job application system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(human_router)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "SmartApply Human-in-the-Loop API",
        "status": "running",
        "endpoints": {
            "role_analysis": "/human/role-analysis",
            "resume_optimization": "/human/resume-optimization", 
            "translation_event": "/human/translation-event"
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    try:
        from app.db.supabase_repo import SupabaseRepo
        
        # Test database connection
        repo = SupabaseRepo()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-08-20T01:30:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)