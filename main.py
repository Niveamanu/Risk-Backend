from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import  studies_router, assessment_router, notification_router, audit_router
import logging
from typing import Dict, Any
from fastapi import Depends, HTTPException 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Create FastAPI app
app = FastAPI(
    title="Risk Assessment Backend API",
    #root_path="/api"
    
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://riskassessment-dev.flourishresearch.com","http://localhost:5173","http://localhost:5174"],  # React frontend origin
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"], # Cache preflight requests for 24 hours
)

# Root endpoint for health checks
@app.get("/")
async def root():
    logger.info("Request: GET /")
    response = {"message": "Risk Assessment Backend API is running", "status": "healthy"}
    logger.info("Response: 200")
    return response

# Include routers
#app.include_router(example_router.router)
app.include_router(studies_router.router , prefix="/api/v1",tags=["Risk Assessment Backend API"])
app.include_router(assessment_router.router , prefix="/api/v1",tags=["Risk Assessment Backend API"])
app.include_router(notification_router.router , prefix="/api/v1",tags=["Risk Assessment Backend API"])
app.include_router(audit_router.router , prefix="/api/v1",tags=["Risk Assessment Backend API"])

 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 