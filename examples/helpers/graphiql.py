import strawberry
import strawberry.utils.graphiql
from io import BytesIO

def graphiql_from(Query, Mutation=None):
    if Mutation:
        schema = strawberry.Schema(query=Query, mutation=Mutation)
    else:
        schema = strawberry.Schema(Query)

    def post(res, req):
        # we can pass whatever we want to context, query, headers or params, cookies etc
        context_value = req.preserve()
        
        buffer = BytesIO()
        def on_data(res, chunk, is_end):   
            buffer.write(chunk)
            if is_end:
                try:
                    body = res.app._json_serializer.loads(buffer.getvalue().decode("utf-8"))
                    res.run_async(graph_ql(res, body, context_value))
                except Exception as err:
                    res.app.trigger_error(err, res, None)
    
        res.grab_aborted_handler()
        res.on_data(on_data)

        async def graph_ql(res, body, context_value):
            query = body["query"]
        
            variables = body.get("variables", None)
            root_value = body.get("rootValue", None)
            operation_name = body.get("operationName", None)

            data = await schema.execute(
                query,
                variables,
                context_value,
                root_value,
                operation_name,
            )

            res.cork_send(
                {
                    "data": (data.data),
                    **({"errors": data.errors} if data.errors else {}),
                    **({"extensions": data.extensions} if data.extensions else {}),
                }
            )

    return post
