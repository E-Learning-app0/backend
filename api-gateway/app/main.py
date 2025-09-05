from fastapi import FastAPI, HTTPException, Depends, Request
import httpx
import time
import datetime
import asyncio
from typing import Dict, Any
from app.core.config import settings

app = FastAPI(
    title="E-Learning API Gateway",
    description="Central gateway for microservices communication",
    version="1.0.0"
)

# Service URLs
SERVICES = {
    "auth": "http://localhost:8000",
    "content": "http://localhost:8080",
    # Add more services as needed
}

# =================== HEALTH CHECK ENDPOINTS ===================

@app.get("/health")
async def gateway_health_check():
    """
    Basic health check for API Gateway to prevent cold starts.
    Can be called without authentication every 2-3 minutes.
    """
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "uptime": time.time()
    }

@app.get("/health/services")
async def services_health_check():
    """
    Check health of all microservices.
    Use this to ensure all services are warm and responsive.
    """
    start_time = time.time()
    service_statuses = {}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check each service health
        for service_name, base_url in SERVICES.items():
            try:
                service_start = time.time()
                response = await client.get(f"{base_url}/health")
                response_time = round((time.time() - service_start) * 1000, 2)
                
                if response.status_code == 200:
                    service_statuses[service_name] = {
                        "status": "healthy",
                        "response_time_ms": response_time,
                        "url": base_url
                    }
                else:
                    service_statuses[service_name] = {
                        "status": "unhealthy",
                        "response_time_ms": response_time,
                        "url": base_url,
                        "error": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                service_statuses[service_name] = {
                    "status": "unreachable",
                    "response_time_ms": -1,
                    "url": base_url,
                    "error": str(e)
                }
    
    # Determine overall status
    all_healthy = all(status["status"] == "healthy" for status in service_statuses.values())
    overall_status = "healthy" if all_healthy else "degraded"
    
    total_response_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": overall_status,
        "service": "api-gateway",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "services": service_statuses,
        "response_time_ms": total_response_time
    }

@app.get("/warmup")
async def warmup_services():
    """
    Warmup endpoint that calls health checks on all services.
    Use this to prevent cold starts across all microservices.
    Should be called every 2-3 minutes by frontend or monitoring.
    """
    return await services_health_check()

# =================== SERVICE PROXY ENDPOINTS ===================

@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def auth_proxy(request: Request, path: str):
    """Proxy requests to auth service"""
    return await proxy_request(request, "auth", path)

@app.api_route("/content/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def content_proxy(request: Request, path: str):
    """Proxy requests to content service"""
    return await proxy_request(request, "content", path)

async def proxy_request(request: Request, service: str, path: str):
    """Generic proxy function for forwarding requests to microservices"""
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    service_url = SERVICES[service]
    url = f"{service_url}/{path}"
    
    # Get request body if exists
    body = await request.body()
    
    # Forward headers (excluding host)
    headers = dict(request.headers)
    headers.pop("host", None)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            return {
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Service timeout")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Service error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
