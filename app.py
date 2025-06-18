from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# CORS: allow only React app at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://regemaill.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated in-memory database
registered_emails = {"test@example.com", "user@site.com"}

# Retrieve APP_SECRET from environment variables
# You can also provide a fallback value
APP_SECRET = os.getenv("APP_SECRET", "default_value")


class EmailRequest(BaseModel):
    email: EmailStr


@app.post("/register")
def register_email(req: EmailRequest, request: Request):
    # 1. Check Origin header
    origin = request.headers.get("origin")
    if origin != "https://regemaill.netlify.app":
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
