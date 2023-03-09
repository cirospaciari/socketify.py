from streaming_form_data import StreamingFormDataParser
from socketify import Response
def get_formdata(res: Response, parser: StreamingFormDataParser):
    _dataFuture = res.app.loop.create_future()

    def is_aborted(res):
        res.aborted = True
        try:
            if not _dataFuture.done():
                _dataFuture.set_result(parser)
        except:
            pass

    def get_chunks(res, chunk, is_end):
        parser.data_received(chunk)
        if is_end:
            _dataFuture.set_result(parser)

    res.on_aborted(is_aborted)
    res.on_data(get_chunks)
    return _dataFuture