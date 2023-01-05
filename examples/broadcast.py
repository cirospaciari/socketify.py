from socketify import App, AppOptions, OpCode, CompressOptions


def ws_open(ws):
    print("A WebSocket got connected!")
    # Let this client listen to topic "broadcast"
    ws.subscribe("broadcast")


def ws_message(ws, message, opcode):
    # Broadcast this message
    ws.publish("broadcast", message, opcode)

app = App()
app.ws(
    "/*",
    {
        "compression": CompressOptions.SHARED_COMPRESSOR,
        "max_payload_length": 16 * 1024 * 1024,
        "idle_timeout": 60,
        "open": ws_open,
        "message": ws_message,
        # The library guarantees proper unsubscription at close
        "close": lambda ws, code, message: print("WebSocket closed"),
        "subscription": lambda ws, topic, subscriptions, subscriptions_before: print(f'subscription/unsubscription on topic {topic} {subscriptions} {subscriptions_before}'),
    },
)
app.any("/", lambda res, req: res.end("Nothing to see here!"))
app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % (config.port)),
)
app.run()
