from socketify import App, AppOptions


#this can be async no problems 
def on_error(error, res, req): 
    #here you can log properly the error and do a pretty response to your clients
    print("Somethind goes %s" % str(error))
    #response and request can be None if the error is in an async function
    if res != None:
        #if response exists try to send something
        res.write_status(500)
        res.end("Sorry we did something wrong")
app = App(AppOptions(key_file_name="./misc/key.pem", cert_file_name="./misc/cert.pem", passphrase="1234"))
app.set_error_handler(on_error)

app.get("/", lambda res, req: res.end("Hello World socketify from Python!"))
app.listen(3000, lambda config: print("Listening on port https://localhost:%d now\n" % config.port))
app.run()