import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from auth import hash_password, verify_password, create_access_token
from database import get_db
from models import User
from schemas import RegisterIn, LoginIn, Token, UserOut
from auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

ADMIN_EMAILS = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "admin@example.com").split(",") if e.strip()]

@router.post("/register", response_model=Token)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    role = "admin" if data.email.lower() in ADMIN_EMAILS else "guest"
    user = User(email=data.email, hashed_password=hash_password(data.password), name=data.name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.from_orm(user))

@router.post("/login", response_model=Token)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.from_orm(user))

@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

@router.get("/google/login")
def google_login():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    from urllib.parse import urlencode
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)

@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    import httpx
    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        token_data = token_resp.json()
        if "access_token" not in token_data:
            raise HTTPException(status_code=400, detail="OAuth token exchange failed")
        userinfo = (await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={"Authorization": f"Bearer {token_data['access_token']}"})).json()
    sub = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name")
    user = db.query(User).filter((User.google_sub == sub) | (User.email == email)).first()
    if not user:
        role = "admin" if email.lower() in ADMIN_EMAILS else "guest"
        user = User(email=email, name=name, google_sub=sub, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.google_sub:
            user.google_sub = sub
            db.commit()
    token = create_access_token({"sub": str(user.id)})
    # redirect to frontend with token
    frontend = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(f"{frontend}/oauth-callback?token={token}")
