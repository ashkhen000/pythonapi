from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import requests

app = FastAPI()

# CORS: allow only React app at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated in-memory database
registered_emails = {"test@example.com", "user@site.com"}

# Shared secret (must match frontend)
APP_SECRET = "KeyOfSecure448877!!!"  # ⚠️ In production, store in env variable


class EmailRequest(BaseModel):
    email: EmailStr


@app.post("/register")
def register_email(req: EmailRequest, request: Request):
    # 1. Check Origin header
    origin = request.headers.get("origin")
    if origin != "http://localhost:3000":
        raise HTTPException(
            status_code=403, detail="Forbidden: Invalid origin")

    # 2. Check secret header
    secret = request.headers.get("x-app-secret")
    if secret != APP_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid token")

    # 3. Check for existing email
    if req.email in registered_emails:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 4. Register and push to Firebase
    registered_emails.add(req.email)

    firebase_url = "https://python-project-a1ebb-default-rtdb.firebaseio.com/emails.json"
    response = requests.post(firebase_url, json={"email": req.email})

    if response.status_code != 200:
        raise HTTPException(
            status_code=500, detail="Failed to save to Firebase")

    return {"message": "Email registered successfully"}
