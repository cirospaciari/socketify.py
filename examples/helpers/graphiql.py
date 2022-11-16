import strawberry
import strawberry.utils.graphiql


def graphiql_from(Query, Mutation=None):
    if Mutation:
        schema = strawberry.Schema(query=Query, mutation=Mutation)
    else:
        schema = strawberry.Schema(Query)

    async def post(res, req):
        # we can pass whatever we want to context, query, headers or params, cookies etc
        context_value = {
            "query": req.get_queries(),
            "headers": req.get_headers(),
            "params": req.get_parameters(),
        }

        # get all incomming data and parses as json
        body = await res.get_json()

        query = body["query"]
        variables = body.get("variables", None)
        root_value = body.get("root_value", None)
        operation_name = body.get("operation_name", None)

        data = await schema.execute(
            query,
            variables,
            context_value,
            root_value,
            operation_name,
        )

        res.cork_end(
            {
                "data": (data.data),
                **({"errors": data.errors} if data.errors else {}),
                **({"extensions": data.extensions} if data.extensions else {}),
            }
        )

    return post
