import dataclasses
import strawberry
import strawberry.utils.graphiql

from socketify import App
from typing import List, Optional


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> Optional[User]:
        return User(name="Hello")


schema = strawberry.Schema(Query)


async def graphiql_post(res, req):
    # we can pass whatever we want to context, query, headers or params, cookies etc
    context_value = req.preserve()

    # get all incoming data and parses as json
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


app = App()
app.get("/", lambda res, req: res.end(strawberry.utils.graphiql.get_graphiql_html()))
app.post("/", graphiql_post)
app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
