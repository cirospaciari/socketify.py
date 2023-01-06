## GraphiQL Support
In [`/src/examples/helper/graphiql.py`](https://github.com/cirospaciari/socketify.py/blob/main/examples/graphiql.py) we implemented an helper for using graphiQL with strawberry.

### Usage
```python
import dataclasses
import strawberry
import strawberry.utils.graphiql

from socketify import App
from typing import List, Optional
from helpers.graphiql import graphiql_from


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> Optional[User]:
        # self.context is the AppRequest
        return User(name="Hello")


app = App()
app.get("/", lambda res, req: res.end(strawberry.utils.graphiql.get_graphiql_html()))
app.post("/", graphiql_from(Query))
# you can also pass an Mutation as second parameter
# app.post("/", graphiql_from(Query, Mutation))
app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
```

### Helper Implementation

```python
import strawberry
import strawberry.utils.graphiql


def graphiql_from(Query, Mutation=None):
    if Mutation:
        schema = strawberry.Schema(query=Query, mutation=Mutation)
    else:
        schema = strawberry.Schema(Query)

    async def post(res, req):
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

    return post

```

### Next [WebSockets and Backpressure](websockets-backpressure.md)