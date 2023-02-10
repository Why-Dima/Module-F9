import os
from aiohttp import web, ClientSession


WS_FILE = os.path.join(os.path.dirname(__file__), 'websocket.html')


async def post_handler(request):
    data = await request.json()
    async with ClientSession().ws_connect("http://127.0.0.1:8080/") as ws:
        await ws.send_str(data["news"])
        await ws.close()
    return web.json_response(data)


async def webhandler(request: web.Request):
    resp = web.WebSocketResponse()
    available = resp.can_prepare(request)
    if not available:
        with open(WS_FILE, 'rb') as fp:
            return web.Response(body=fp.read(), content_type="text/html")
    
    await resp.prepare(request)

    try:
        print('Someone joined.')
        request.app['sockets'].append(resp)

        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                for ws in request.app['sockets']:
                    if ws not in resp:
                        await ws.send_str(msg.data)
            else:
                return resp
        
        return resp

    finally:
        request.app["sockets"].remove(resp)
        print("Someone disconnected.")

        
async def on_shutdown(app: web.Application):
    for ws in app['sockets']:
        await ws.close()


def init():
    app = web.Application()
    app['sockets'] = []
    app.router.add_route("GET" ,'/', webhandler)
    app.router.add_route("POST", "/news", post_handler)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host="127.0.0.1", port="8080")


if __name__ == "__main__":
    init()