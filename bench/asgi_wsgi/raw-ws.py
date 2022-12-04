from socketify import ASGI

async def app(scope, receive, send):
    
    # handle non websocket
    if scope['type'] != 'websocket':
        
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'text/plain'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': b'Connect via ws protocol!',
        })
    protocols = scope['subprotocols']
    
    scope = await receive()
    # get connection
    assert scope['type'] == 'websocket.connect'
    # accept connection
    await send({
        'type': 'websocket.accept',
        'subprotocol': protocols[0] if len(protocols) > 0 else None 
    })
    # get data
    while True:
        scope = await receive()
        type = scope['type']
        # disconnected!
        if type == 'websocket.disconnect':
            print("disconnected!", scope)
            break

        # echo!
        await send({
            'type': 'websocket.send',
            'bytes': scope.get('bytes', None),
            'text': scope.get('text', '')
        })





if __name__ == "__main__":
    ASGI(app).listen(4001, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()

# python3 -m gunicorn test:app -w 1 -k uvicorn.workers.UvicornWorker