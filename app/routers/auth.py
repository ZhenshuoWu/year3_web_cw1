from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.utils.auth import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        400: {"description": "Username or email already registered",
              "content": {"application/json": {"example": {"detail": "Username already registered"}}}},
    }
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account. Username and email must be unique."""
    # Check if username or email already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token,
    summary="Login",
    responses={
        401: {"description": "Invalid credentials",
              "content": {"application/json": {"example": {"detail": "Incorrect username or password"}}}},
    }
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with username and password to receive a JWT access token. Use the token as `Bearer <token>` in the Authorization header."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
