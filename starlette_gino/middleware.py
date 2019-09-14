import typing

from gino import Gino
from gino import create_engine
from gino.exceptions import UninitializedError
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
        try:
            self.engine = self.db.bind
        except UninitializedError:
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
            scope["database"] = self.engine
            await inner_app(scope, receiver, send)
            return

        if not self.engine:
            self.engine = await create_engine(self.database_url, **self.kwargs)
        scope["database"] = self.engine
        await self.app(scope, receive, send)
