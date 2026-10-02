import jwt

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils import token
from app.configs.rediss import redis_client
from app.configs.auth_paths import PUBLIC_PATHS, PUBLIC_PREFIXES


class AuthMiddleware(BaseHTTPMiddleware):
    '''Middleware for checking if the user is authenticated to access the endpoint. This uses verification of access token send in 'Authorization' header. If not then it will send a JSON respone with 401 error/status code.'''


    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)

        if self._is_public(path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return self._unauthorized("Missing or invalid Authorization header.")

        access_token = auth_header.split(" ", 1)[1]

        # Decode access token.
        try:
            payload = token.decode_token(access_token)

        except jwt.ExpiredSignatureError:
            return self._unauthorized("Access token expired.")
        
        except jwt.InvalidTokenError:
            return self._unauthorized("Invalid token.")

        if payload.get("type") != "access":
            return self._unauthorized("Invalid token type.")

        # Token is blocked
        if await redis_client.exists(f"denylist:{payload['jti']}"):
            return self._unauthorized("Token has been revoked.")

    
        request.state.user_id = payload["sub"]

        return await call_next(request)
    

    def _is_public(self, path: str) -> bool:
        '''Checks if the request is for public paths i.e. paths which do not require any authentication.'''

        if path in PUBLIC_PATHS:
            return True
        
        if path.endswith("/display-picture"):   
            return True
        
        return any(path.startswith(p) for p in PUBLIC_PREFIXES)


    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        '''Sends JSON response in case if the user is unauthorized.'''
        return JSONResponse(
            status_code=401,
            content={
                "status": "failed", 
                "message": detail, 
                "data": None
            },
        )
