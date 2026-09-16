from fastapi import FastAPI
import uvicorn
from api.handlers import router
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Star Systems")

app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Запуск сервера. reload=True автоматически перезапускает сервер при изменении кода
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
