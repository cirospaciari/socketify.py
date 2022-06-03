from socketify import App

###
# We always recomend check res.aborted in async operations 
###

def upload(res, req):
    print(f"Posted to {req.get_url()}")

    def on_data(res, chunk, is_end):
        print(f"Got chunk of data with length {len(chunk)}, is_end: {is_end}")
        if (is_end):
            res.end("Thanks for the data!")

    res.on_data(on_data)

async def upload_chunks(res, req):
    print(f"Posted to {req.get_url()}")
    #await all the data, returns received chunks if fail (most likely fail is aborted requests)
    data = await res.get_data()
    
    print(f"Got {len(data)} chunks if data!")
    for chunk in data:
        print(f"Got chunk of data with length {len(chunk)}")
        
    #We respond when we are done
    res.end("Thanks for the data!")

async def upload_json(res, req):
    print(f"Posted to {req.get_url()}")
    #await all the data and parses as json, returns None if fail
    people = await res.get_json()

    if isinstance(people, list) and isinstance(people[0], dict):
        print(f"First person is named: {people[0]['name']}")
        
    #We respond when we are done
    res.end("Thanks for the data!")

async def upload_text(res, req):
    print(f"Posted to {req.get_url()}")
    #await all the data and decode as text, returns None if fail
    text = await res.get_text() #first parameter is the encoding (default utf-8)
    
    print(f"Your text is ${text}")
        
    #We respond when we are done
    res.end("Thanks for the data!")



app = App()
app.post("/", upload)
app.post("/chunks", upload_chunks)
app.post("/json", upload_json)
app.post("/text", upload_text)

app.any("/*", lambda res,_: res.write_status(404).end("Not Found"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()