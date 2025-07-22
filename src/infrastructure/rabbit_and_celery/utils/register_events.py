from fastapi import FastAPI
import asyncio


def register_events(app: FastAPI, rabbit_listener):
    @app.on_event("startup")
    async def on_startup():
        if rabbit_listener and hasattr(rabbit_listener, "start"):
            maybe_coro = rabbit_listener.start()
            if asyncio.iscoroutine(maybe_coro):
                await maybe_coro

    @app.on_event("shutdown")
    async def on_shutdown():
        if rabbit_listener and hasattr(rabbit_listener, "stop"):
            maybe_coro = rabbit_listener.stop()
            if asyncio.iscoroutine(maybe_coro):
                await maybe_coro
