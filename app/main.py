import uvicorn
from fastapi import FastAPI
from app.api.routes import router as auth_router

app = FastAPI(debug=True)
app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
