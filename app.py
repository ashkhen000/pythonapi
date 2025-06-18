from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://regemaill.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APP_SECRET = os.getenv("APP_SECRET", "default_value")
RECAPTCHA_SECRET = os.getenv(
    "RECAPTCHA_SECRET", "6Lfm3mMrAAAAABPoMgEM2Qn2skpYwU2wHAsIflzF")


class EmailRequest(BaseModel):
    email: EmailStr
    recaptcha_token: str


def verify_recaptcha(token: str) -> bool:
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": RECAPTCHA_SECRET,
        "response": token
    }
    r = requests.post(url, data=data)
    result = r.json()
    return result.get("success", False)


@app.post("/register")
def register_email(req: EmailRequest, request: Request):
    origin = request.headers.get("origin")
    if origin != "https://regemaill.netlify.app":
        raise HTTPException(
            status_code=403, detail="Forbidden: Invalid origin")

    if not verify_recaptcha(req.recaptcha_token):
        raise HTTPException(
            status_code=400, detail="reCAPTCHA verification failed")

    firebase_url = "https://python-project-a1ebb-default-rtdb.firebaseio.com/emails.json"
    try:
        firebase_response = requests.get(firebase_url)
        if firebase_response.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Failed to fetch from Firebase")

        existing_data = firebase_response.json() or {}
        existing_emails = {item['email']
                           for item in existing_data.values() if 'email' in item}

        if req.email in existing_emails:
            raise HTTPException(
                status_code=400, detail="Email already registered")

        post_response = requests.post(firebase_url, json={"email": req.email})
        if post_response.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Failed to save to Firebase")

        return {"message": "Email registered successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
