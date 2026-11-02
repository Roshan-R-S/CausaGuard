"""Small ASGI boundary: cap bodies before JSON parsing and bound concurrent mock runs."""

import asyncio

from starlette.responses import JSONResponse

from causaguard.llm import strict_json


class RequestLimits:
    def __init__(self, app, max_body=1_048_576, max_active=4):
        self.app, self.max_body, self.max_active = app, max_body, max_active
        self.active = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return
        limited = scope["path"] in ("/recommend", "/llm/demo", "/llm/replay")
        if limited and self.active >= self.max_active:
            await JSONResponse({"detail": "mock execution capacity exceeded"}, 429)(scope, receive, send)
            return
        if limited:
            self.active += 1
        try:
            body = bytearray()
            deadline = asyncio.get_running_loop().time() + 30
            while True:
                remaining = deadline - asyncio.get_running_loop().time()
                try:
                    message = await asyncio.wait_for(receive(), timeout=max(0, remaining))
                except TimeoutError:
                    await JSONResponse({"detail": "request body timeout"}, 408)(scope, receive, send)
                    return
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                if len(body) + len(chunk) > self.max_body:
                    await JSONResponse({"detail": "request body too large"}, 413)(scope, receive, send)
                    return
                body.extend(chunk)
                if not message.get("more_body", False):
                    break
            try:
                strict_json(body.decode("utf-8"), max_bytes=self.max_body)
            except ValueError:
                await JSONResponse({"detail": "invalid or excessive JSON structure"}, 422)(scope, receive, send)
                return
            delivered = False

            async def bounded_receive():
                nonlocal delivered
                if delivered:
                    return await receive()
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}

            await self.app(scope, bounded_receive, send)
        finally:
            if limited:
                self.active -= 1
