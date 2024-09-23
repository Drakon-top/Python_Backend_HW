import uvicorn
import json
import math
from urllib import parse


async def send_response(send, status_code=200, dump=None):
    if dump is None:
        dump = {"message": "none"}
    await send({
        "type": "http.response.start",
        "status": status_code,
        "headers": [
            [b"content-type", b"application/json"],
        ]
    })
    await send({
        "type": "http.response.body",
        "body": json.dumps(dump).encode("utf-8"),
    })


async def fibonacci(scope, receive, send):
    _list = scope["path"].split("/")
    number = int(_list[2])
    if number < 0:
        await send_response(send, 400)
        return

    a, b = 0, 1
    if number == 0:
        result = a
    else:
        for i in range(number - 1):
            a, b = b, a + b
        result = b
    return result


async def factorial(scope, receive, send):
    _dict = parse.parse_qs(scope['query_string'].decode("ascii"))
    number = int(_dict['n'][0])
    if number < 0:
        await send_response(send, 400)
        return

    return math.factorial(number)


async def mean(scope, receive, send):
    event = await receive()
    body = event.get('body', b'')
    data = json.loads(body)
    numbers = list(map(lambda x: float(x), data))
    if len(numbers) == 0:
        await send_response(send, 400)
        return

    return sum(numbers) / len(numbers)


async def universal(scope, receive, send, fun):
    try:
        result = await fun(scope, receive, send)
        if result is None:
            return
        dump = {
            "result": result
        }
        await send_response(send, 200, dump)
    except Exception as e:
        print(e)
        await send_response(send, 422)


paths = {
    "fibonacci": fibonacci,
    "factorial": factorial,
    "mean": mean,
}


async def app(scope, receive, send) -> None:
    if scope["type"] != "http" or scope["method"] != "GET":
        await send_response(send, 404)
        return
    _list = scope["path"].split("/")
    if _list[1] in paths:
        await universal(scope, receive, send, paths[_list[1]])
    else:
        await send_response(send, 404)


class App:
    def __init__(self, port=8000, log_level="info"):
        self.config = uvicorn.Config(app, port=port, log_level=log_level)
        self.server = uvicorn.Server(self.config)

    def run(self):
        self.server.run()

    def close(self):
        #  I haven't found any information on how to stop the server.
        pass


if __name__ == "__main__":
    app = App()
    try:
        app.run()
    except Exception as ex:
        app.close()
