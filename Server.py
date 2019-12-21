import asyncio
import json
import logging
import sys

from hypercorn import Config
from hypercorn.asyncio import serve
from quart import Quart, websocket

from ServerTools import Tools

app = Quart(__name__)


def rtn(code: int, message: str):
    return json.dumps({"code": code, "message": message})


async def auth(str_json) -> tuple:
    try:
        d = json.loads(str_json)
    except json.JSONDecodeError:
        return False, "NoJSON"
    else:
        if "username" in d and "password" in d:
            return await tools.login(d["username"], d["password"])


@app.websocket("/client")
async def client():
    while True:
        r = await websocket.receive()
        rt = await auth(r)
        if rt[0]:
            print(rt[1], "Login!")
            while True:
                r = await websocket.receive()
                try:
                    dr = json.loads(r)
                except json.JSONDecodeError:
                    await websocket.send(rtn(1, "NoJSON"))
                else:
                    await websocket.send(json.dumps(dr))
        else:
            await websocket.send(rtn(1, rt[1]))


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    config = Config()
    config.bind = ["0.0.0.0:5700", ":::5700"]
    config.access_logger = logger
    config.error_logger = logger
    config.use_reloader = True
    tools = Tools(logger)
    asyncio.run(serve(app=app, config=config))
