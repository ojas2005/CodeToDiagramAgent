from fastapi import FastAPI, HTTPException
from .auth import authenticate, create_session

app = FastAPI()


@app.post("/login")
def login(payload: dict):
    user = authenticate(payload["username"], payload["password"])
    if user is None:
        raise HTTPException(status_code=401)
    return {"session": create_session(user["id"])}
