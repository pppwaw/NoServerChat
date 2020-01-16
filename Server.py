import asyncio
import threading
import json
import logging
import sys
import time
import multiprocessing

import quart
from hypercorn import Config
from hypercorn.asyncio import serve
from quart import Quart, websocket, Blueprint
from ServerTools import *

websocket: quart.wrappers.request.Websocket

app = Quart(__name__)


def rtn(code: int = 0, message: str = "OK"):
    return json.dumps({"code": code, "message": message})


async def auth(str_json) -> tuple:
    try:
        d = json.loads(str_json)
    except json.JSONDecodeError:
        return False, "NoJSON"
    else:
        if "username" in d and "password" in d:
            return await ctools.login(d["username"], d["password"])


@app.websocket("/client/send")
async def client_recv():
    while True:
        r = await websocket.receive()
        rt = await auth(r)
        logger.debug((r, rt))
        if rt[0]:
            session_id = rt[1]
            name = ctools.session_id[session_id]
            await websocket.send(rtn(0, session_id))
            print(name, "Login!")
            queue = ctools.queues[name]
            while True:
                r = await websocket.receive()
                print(r)
                try:
                    dr = json.loads(r)
                except json.JSONDecodeError:
                    await websocket.send(rtn(1, "NoJSON"))
                else:
                    re = await ctools.serve(dr, name)
                    if re[1] == "break":
                        break
                    await websocket.send(rtn(int(not re[0]), re[1]))

        else:
            await websocket.send(rtn(1, rt[1]))


@app.websocket("/client/recv/<name>")
async def client_send(name):
    if name in ctools.user:
        await websocket.send(rtn())
        queue = ctools.user[name]
        while True:
            r = await queue.get()
            await websocket.send(json.dumps(r))
    else:
        await websocket.send(rtn(1, "No Login"))


@app.websocket("/server/send")
async def server_recv():
    while True:
        r = await websocket.receive()
        try:
            rt = json.loads(r)
        except:
            await websocket.send(json.dumps(rtn(1, "NoJSON")))
        else:
            if "name" in rt:
                j = await stools.join(rt["name"])
                if j[0]:
                    name = rt["name"]
                    await websocket.send(rtn(0, stools.name))
                    print(name, "Join!")
                    while True:
                        r = await websocket.receive()
                        try:
                            dr = json.loads(r)
                        except json.JSONDecodeError:
                            await websocket.send(rtn(1, "NoJSON"))
                        else:
                            re = await stools.serve(dr, name)
                            if re[1] == "break":
                                break
                            await websocket.send(rtn(int(not re[0]), re[1]))
                else:
                    await websocket.send(rtn(not j[0], j[1]))
            else:
                await websocket.send(rtn(1, "No name"))


@app.websocket("/server/recv/<name>")
async def server_send(name):
    if name in stools.server:
        await websocket.send(rtn())
        queue = stools.server[name]
        while True:
            r = await queue.get()
            await websocket.send(json.dumps(r))
    else:
        await websocket.send(rtn(1, "No Join"))


def get_tools(user_table, logger):
    ctools = ClientTools(user_table, logger)
    sstools = ServerSTools("pppwaw", ctools, logger)
    sctools = ServerCTools(sstools, logger)
    ctools.set_stools(sstools)
    sstools.set_url_queue(sctools.urlqueue)
    return ctools, sstools, sctools


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    config = Config()
    config.bind = ["0.0.0.0:5700", ":::5700"]
    config.access_logger = logger
    config.error_logger = logger
    config.use_reloader = False
    ctools, stools, sctools = get_tools("user.json", logger)
    web = lambda: asyncio.run(serve(app=app, config=config))
    sts = lambda: sctools.main()  # servertoserver
    pool = [multiprocessing.Process(target=web), multiprocessing.Process(target=sts)]
    [i.start() for i in pool]
    [i.join() for i in pool]
