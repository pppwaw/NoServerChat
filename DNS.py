from quart import Quart, request
import json, asyncio, logging, sys
from hypercorn import Config
from hypercorn.asyncio import serve

app = Quart(__name__)
addrs = []


def rtn(code: int = 0, message: str = "OK"):
    return json.dumps({"code": code, "message": message})


@app.route("/dns")
async def dns():
    return json.dumps(addrs)


@app.route("/dns/add", ["GET", "POST"])
async def add():
    # form = {}
    form = (await request.get_data()).decode(encoding="UTF-8")
    try:
        form = json.loads(form)
    except:
        return rtn(1, "noJSON")
    else:
        try:
            addrs.append({"name": form["name"], "ipv6": form["ipv6"], "ipv4": form["ipv4"]})
        except:
            if "name" not in form:
                return rtn(1, "no name")
            elif "ipv6" not in form:
                return rtn(1, "no ipv6")
            elif "ipv4" not in form:
                return rtn(1, "no ipv4")
            else:
                return rtn(1, "Unknown Error")
    return rtn()


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    config = Config()
    config.bind = ["0.0.0.0:5699", ":::5699"]
    config.access_logger = logger
    config.access_log_format = "%(h)s %(r)s %(s)s %(b)s %(D)s"
    config.error_logger = logger
    asyncio.run(serve(app=app, config=config))
    # app.run(host="0.0.0.0",port=5699,use_reloader=True)
