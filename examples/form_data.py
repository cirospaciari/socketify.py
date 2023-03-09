from socketify import App
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget, FileTarget
app = App()
router = app.router()

@router.post("/")
async def upload(res, req):
    print(f"Posted to {req.get_url()}")
    parser = StreamingFormDataParser(headers=req.get_headers())
    name = ValueTarget()
    parser.register('name', name)
    file = FileTarget('/tmp/file')
    file2 = FileTarget('/tmp/file2')
    parser.register('file', file)
    parser.register('file2', file2)


    def on_data(res, chunk, is_end):   
        parser.data_received(chunk)
        if is_end:
            res.cork(on_finish)


    def on_finish(res):
        print(name.value)
        
        print(file.multipart_filename)
        print(file.multipart_content_type)

        print(file2.multipart_filename)
        print(file2.multipart_content_type)

        res.end("Thanks for the data!")

    res.on_data(on_data)


@router.any("*")
def not_found(res, _):
    res.write_status(404).end("Not Found")

app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
