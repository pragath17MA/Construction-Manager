import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import schemas, models
from app.core import security
from app.core.database import get_db
from app.api import deps
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    hashed_password = security.get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=schemas.Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    access_token = security.create_access_token(
        subject=user.email,
        role=user.role.value
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_name": user.full_name
    }

@router.post("/forgot-password")
def forgot_password(
    req: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Standard generic response to prevent user enumeration
        return {"message": "If this email is registered, a password reset link has been generated."}
    
    reset_token = str(uuid.uuid4())
    user.password_reset_token = reset_token
    # Save naive datetime using utcnow for database compatibility
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    return {
        "message": "Password reset token generated successfully.",
        "dev_token": reset_token
    }

@router.post("/reset-password")
def reset_password(
    req: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.password_reset_token == req.token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Compare with current time
    now = datetime.utcnow()
    if user.password_reset_expires and user.password_reset_expires < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
        
    user.hashed_password = security.get_password_hash(req.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    return {"message": "Password has been reset successfully."}

@router.get("/me", response_model=schemas.UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user)
):
    return current_user

@router.get("/users", response_model=list[schemas.UserResponse])
def read_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get all active users in the system (used for project member selector).
    """
    return db.query(User).all()

@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_database(db: Session = Depends(get_db)):
    """
    Seeds the database with structured mock data for construction dashboards,
    risks, materials, and worker schedules.
    """
    from app.utils.seed import run_seed
    try:
        run_seed(db)
        return {"status": "success", "message": "Database seeded successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database seeding failed: {str(e)}"
        )
