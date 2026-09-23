import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from starlette.responses import Response

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Retrieve or generate a request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Attach to request state for downstream use
        request.state.request_id = request_id
        
        # Process the request
        response = await call_next(request)
        
        # Inject it into the response headers
        response.headers["X-Request-ID"] = request_id
        return response
