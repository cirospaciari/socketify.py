
# Plugins / Extensions

You can add more functionality to request, response, and websocket objects, for this you can use `app.register(extension)` to register an extension.
Be aware that using extensions can have a performance impact and using it with `request_response_factory_max_items`, `websocket_factory_max_items`
or the equivalent on CLI `--req-res-factory-maxitems`, `--ws-factory-maxitems` will reduce this performance impact.

Extensions must follow the signature `def extension(request, response, ws)`, request, response, and ws objects contain `method` decorator that binds a method to an instance,
and also a `property(name: str, default_value: any = None)` that dynamic adds an property to the instance.

```python
from socketify import App, OpCode

app = App()

def extension(request, response, ws):
    @request.method
    async def get_user(self):
        token = self.get_header("token")
        return { "name": "Test" } if token else { "name", "Anonymous" }
    
    @response.method
    def msgpack(self, value: any):
        self.write_header(b'Content-Type', b'application/msgpack')
        data = msgpack.packb(value, default=encode_datetime, use_bin_type=True)
        return self.end(data)
    
    @ws.method
    def send_pm(self, to_username: str, message: str):
        user_data = self.get_user_data()
        pm_topic = f"pm-{to_username}+{user_data.username}"
        
        # if topic exists just send the message
        if app.num_subscribers(pm_topic) > 0:
            # send private message
            return self.publish(pm_topic, message, OpCode.TEXT)
        
        # if the topic not exists create it and signal the user
        # subscribe to the conversation
        self.subscribe(pm_topic)
        # signal user that you want to talk and create an pm room
        # all users must subscribe to signal-{username}
        self.publish(f"signal-{to_username}", { 
            "type": "pm", 
            "username": user_data.username, 
            "message": message 
        }, OpCode.TEXT)
    # this property can be used on extension methods and/or middlewares
    request.property("cart", [])

# extensions must be registered before routes
app.register(extension)
```

### Next [SSL](ssl.md)
