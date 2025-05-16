import uvicorn
from fastapi import FastAPI
from app.api.routes import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(debug=True)
app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
