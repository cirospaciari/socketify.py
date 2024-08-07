## Uploading or Getting the Posting data

### Manually getting the chunks
Using `res.on_data` you can grab any chunk sended to the request

```python
def upload(res, req):
    def on_data(res, chunk, is_end):
        print(f"Got chunk of data with length {len(chunk)}, is_end: {is_end}")
        if is_end:
            res.cork_end("Thanks for the data!")

    res.on_data(on_data)
```

### Getting it in an single call
We created an `res.get_data()` to get all data at once internally will create an BytesIO for you.

```python
async def upload_chunks(res, req):
    print(f"Posted to {req.get_url()}")
    # await all the data, returns received chunks if fail (most likely fail is aborted requests)
    data = await res.get_data()

    print(f"Got {len(data.getvalue())} bytes of data!")
    
    # We respond when we are done
    res.cork_end("Thanks for the data!")
```
### Getting utf-8/encoded data
Similar to `res.get_data()`, `res.get_text(encoding="utf-8")` will decode as text with the encoding you want.
```python
async def upload_text(res, req):
    print(f"Posted to {req.get_url()}")
    # await all the data and decode as text, returns None if fail
    text = await res.get_text()  # first parameter is the encoding (default utf-8)

    print(f"Your text is ${text}")

    # We respond when we are done
    res.cork_end("Thanks for the data!")
```

### Getting JSON data
Similar to `res.get_data()`, `res.get_json()` will decode the json as dict.
```python
async def upload_json(res, req):
    print(f"Posted to {req.get_url()}")
    # await all the data and parses as json, returns None if fail
    info = res.get_json()

    print(info)


    # We respond when we are done
    res.cork_end("Thanks for the data!")
```

### Getting application/x-www-form-urlencoded data
Similar to `res.get_data()`, `res.get_form_urlencoded(encoding="utf-8")` will decode the application/x-www-form-urlencoded as dict.

```python
async def upload_urlencoded(res, req):
    print(f"Posted to {req.get_url()}")
    # await all the data and decode as application/x-www-form-urlencoded, returns None if fails
    form = await res.get_form_urlencoded()# first parameter is the encoding (default utf-8)

    print(f"Your form is ${form}")

    # We respond when we are done
    res.cork_end("Thanks for the data!")
```
### Dynamic check content-type
You always can check the header Content-Type to dynamic check and convert in multiple formats.

```python
async def upload_multiple(res, req):
    print(f"Posted to {req.get_url()}")
    content_type = req.get_header("content-type")
    # we can check the Content-Type to accept multiple formats
    if content_type == "application/json":
        data = res.get_json()
    elif content_type == "application/x-www-form-urlencoded":
        data = await res.get_form_urlencoded()
    else:
        data = await res.get_text()

    print(f"Your data is ${data}")

    # We respond when we are done
    res.cork_end("Thanks for the data!")
```

### Next [Streaming Data](streaming-data.md)