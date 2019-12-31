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
    return json.dumps({"code": code, "message": str(message)})


async def auth(str_json) -> tuple:
    try:
        d = json.loads(str_json)
    except json.JSONDecodeError:
        return False, "NoJSON"
    else:
        if "username" in d and "password" in d:
            return await tools.login(d["username"], d["password"])


@app.websocket("/client/send")
async def recv():
    while True:
        r = await websocket.receive()
        rt = await auth(r)
        logger.debug((r, rt))
        if rt[0]:
            session_id = rt[1]
            await websocket.send(rtn(0, session_id))
            print(tools.session[session_id], "Login!")
            while True:
                r = await websocket.receive()
                try:
                    dr = json.loads(r)
                except json.JSONDecodeError:
                    await websocket.send(rtn(1, "NoJSON"))
                else:
                    dr["session_id"] = session_id
                    re = await tools.serve(dr)
                    if re[1] == "break":
                        break
                    await websocket.send(rtn(int(re[0]), re[1]))

        else:
            await websocket.send(rtn(1, rt[1]))


@app.websocket("/client/recv/<session_id>")
async def send(session_id):
    print(type(session_id))
    if session_id not in tools.session_id:
        await websocket.send(rtn(1, "No Login"))
    else:
        await websocket.send(rtn(0, "Ok"))
        queue = tools.queues[session_id]
        while True:
            if session_id in tools.session_id:
                r = await queue.get()
                await websocket.send(r)


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
