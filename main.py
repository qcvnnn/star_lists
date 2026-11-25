from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from core.current_user import redis_client
from db.session import engine
import uvicorn
from api.star_list import router
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(
    title="Звёздные системы",
    version="4.0",
    description="Вход через POST /api/star_list/users/login устанавливает cookie session_id. "
                "Swagger отправляет её автоматически на том же адресе. "
                "Каталог и лента доступны гостю; действия создателя требуют входа. "
                "В Postman передайте Cookie: session_id=значение во вкладке Headers.",
    lifespan=lifespan,
)

@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException):
    return Response(status_code=exc.status_code, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    return Response(status_code=422)


@app.exception_handler(Exception)
async def handle_server_error(request: Request, exc: Exception):
    return Response(status_code=500)


app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")

def custom_openapi():
    if app.openapi_schema is None:
        schema = get_openapi(
            title=app.title, version=app.version,
            description=app.description, routes=app.routes,
        )
        for path in schema["paths"].values():
            for operation in path.values():
                if not isinstance(operation, dict):
                    continue
                for code, response in operation.get("responses", {}).items():
                    if code.isdigit() and int(code) >= 400:
                        response["description"] = ""
                        response.pop("content", None)
        app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    # Запуск сервера. reload=True автоматически перезапускает сервер при изменении кода
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
