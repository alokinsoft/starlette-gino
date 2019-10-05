import typing

from gino import Gino
from sqlalchemy.engine.url import URL

from .types import Scope, Receive, Send, ASGIApp, Message


class DatabaseMiddleware:
    engine = None

    def __init__(self, app: ASGIApp, db: Gino, database_url: typing.Union[URL, str] = None, **kwargs) -> None:
        self.db = db
        self.database_url = database_url
        self.app = app
        self.kwargs = kwargs

    async def database_startup(self) -> None:
        if not self.engine:
            self.engine = await self.db.set_bind(self.database_url, **self.kwargs)

    async def database_shutdown(self) -> None:
        await self.db.pop_bind().close()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def receiver() -> Message:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await self.database_startup()
            elif message["type"] == "lifespan.shutdown":
                await self.database_shutdown()
            return message

        inner_app = self.app

        if scope['type'] == 'lifespan':
            await inner_app(scope, receiver, send)
            return

        if scope['type'] == 'http':
            scope['connection'] = await self.db.acquire(lazy=True)
            try:
                await self.app(scope, receive, send)
            finally:
                conn = scope.pop('connection', None)
                if conn is not None:
                    await conn.release()
            return
