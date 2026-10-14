from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.password import hash_password, verify_password
from app.services.tokens import TokenConfigError, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_in: UserRegister,
    db: Session = Depends(get_db),
):
    email = user_in.email.strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email Already Registered",
        )

    user = User(
        email=email,
        password_hash=hash_password(user_in.password),
        role="viewer",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email Already Registered",
        ) from None

    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    user_in: UserLogin,
    db: Session = Depends(get_db),
):
    email = user_in.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Email or Password",
        )

    try:
        access_token = create_access_token(user.id)
    except TokenConfigError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication Service Unavailable",
        ) from None

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
