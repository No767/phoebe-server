#!/usr/bin/env python3

from contextlib import asynccontextmanager
from fastapi import FastAPI
import db
import api
import uvicorn
import argparse
from fastapi_pagination import add_pagination
from api import chat


@asynccontextmanager
async def with_init(_: FastAPI):
    await db.init_db()
    await chat.broadcast.connect()
    yield
    await chat.broadcast.disconnect()


app = FastAPI(lifespan=with_init)
app.include_router(api.router)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="py-rest-template")
    parser.add_argument("-H", "--host", default="127.0.0.1", help="The host to bind to")
    parser.add_argument("-p", "--port", default=5765, help="Port to bind to", type=int)
    parser.add_argument("--database", default="database.db", help="Path to database")
    parser.add_argument(
        "--echo-sql",
        action="store_true",
        help="Print SQL queries to stdout",
    )

    args = parser.parse_args()
    db.set_sqlite_path(args.database)
    db.set_echo(args.echo_sql)
    add_pagination(app)

    uvicorn.run(app, host=args.host, port=args.port)
