from quart import Quart, websocket
import json, asyncio, logging, sys
from hypercorn import Config
from hypercorn.asyncio import serve
from .ServerTools import Tools
app = Quart(__name__)
up = {"asd": "123"}


def rtn(code: int, message: str):
    return json.dumps({"code": code, "message": message})


async def auth(strjson) -> tuple:
    try:
        d = json.loads(strjson)
    except:
        return False, ""
    else:
        if "username" in d and "password" in d:
            if up[d["username"]] == d["password"]:
                return True, d["username"]


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
                except:
                    await websocket.send("NoJSON")
                else:
                    await websocket.send(json.dumps(dr))
        else:
            await websocket.send(rtn(1, "Invalid username or password"))


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
