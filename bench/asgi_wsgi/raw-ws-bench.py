from socketify import ASGI

clients = set([])
remaining_clients = 16

async def broadcast(message):
    for send in clients:
        await send({
            'type': 'websocket.send',
            'text': message
        })
    
async def app(scope, receive, send):
    global remaining_clients

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
    # handle websocket
    protocols = scope['subprotocols']
    
    scope = await receive()
    # get connection
    assert scope['type'] == 'websocket.connect'
    # accept connection
    await send({
        'type': 'websocket.accept',
        'subprotocol': protocols[0] if len(protocols) > 0 else None 
    })
    clients.add(send)
    remaining_clients -= 1
    print("remaining_clients", remaining_clients)

    if remaining_clients == 0:
        await broadcast("ready")

    
    # get data
    while True:
        scope = await receive()
    
        type = scope['type']
        # disconnected!
        if type == 'websocket.disconnect':
            remaining_clients += 1
            print("remaining_clients", remaining_clients)
            break
        
        await broadcast(scope.get('text', ''))
        




if __name__ == "__main__":
    ASGI(app).listen(4001, lambda config: print(f"Listening on port http://localhost:{config.port} now\n")).run()


# python3 -m gunicorn test-ws-bench:app -b 127.0.0.1:4001 -w 1 -k uvicorn.workers.UvicornWorker
