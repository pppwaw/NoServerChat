from quart import Quart, websocket
import json, asyncio, logging, sys
from hypercorn import Config
from hypercorn.asyncio import serve

app = Quart(__name__)


@app.websocket("/client")
def client():
    pass  # websocket


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    config = Config()
    config.bind = ["0.0.0.0:5700", ":::5700"]
    config.access_logger = logger
    config.error_logger = logger
    asyncio.run(serve(app=app, config=config))
    # app.run(host="0.0.0.0",port=5699,use_reloader=True)
