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
