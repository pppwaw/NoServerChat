from quart import Quart, request
import json, asyncio, logging, sys
from hypercorn import Config
from hypercorn.asyncio import serve

app = Quart(__name__)
addrs = []


def msg(code: int = 0, message: str = "OK"):
    return json.dumps({"code": code, "message": message})


@app.route("/dns")
def dns():
    return json.dumps(addrs)


@app.route("/add")
def add():
    # form = {}
    form = (request.get_data()).decode(encoding="UTF-8")
    try:
        form = json.loads(form)
    except:
        return msg(1, "noJSON")
    else:
        try:
            addrs.append({"name": form["name"], "ips": form["ips"]})
        except:
            if "name" not in form:
                return msg(1, "no name")
            elif "ips" not in form:
                return msg(1, "no ips")
            else:
                return msg(1, "Unknown Error")
    print(form)
    return msg()


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
