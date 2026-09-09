"""Accounts: signup, login, your own profile, and the admin-only user list.

Almost all of this follows CaseDesk's src/routers/auth.py. The one real
difference is signup: in CaseDesk only an admin can create an account, here
anyone can - but only ever as a plain "user". The admin comes from
scripts/seed.py.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, now
from app.models import User
from app.schemas import (
    PasswordChange,
    ProfileOut,
    ProfileUpdate,
    TokenOut,
    UserLogin,
    UserOut,
    UserSignup,
    UserUpdate,
)
from app.security import (
    create_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)

auth_router = APIRouter()


@auth_router.post("/auth/signup", response_model=UserOut, status_code=201)
def signup(body: UserSignup, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == body.email.lower()).first()

    if existing_user:
        raise HTTPException(status_code=409,
                            detail="Email already registered")

    new_user = User(
        name=body.name,
        # Stored lowercase, and every lookup lowercases too - otherwise
        # "Ali@x.com" and "ali@x.com" would be two different accounts.
        email=body.email.lower(),
        # Hardcoded, NOT taken from the request. This is the whole reason
        # UserSignup has no role field.
        role="user",
        password_hash=hash_password(body.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@auth_router.post("/auth/login", response_model=TokenOut)
def login(body: UserLogin, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        User.email == body.email.lower(),
        User.deleted_at.is_(None),
    ).first()

    # One message for both "no such email" and "wrong password", on purpose.
    # Two different messages would let anyone find out which emails exist.
    if not existing_user or not verify_password(body.password, existing_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({
        "sub": str(existing_user.id),
        "ver": existing_user.token_version,
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@auth_router.get("/me", response_model=ProfileOut)
def current_profile(current_user: User = Depends(get_current_user)):
    # The frontend asks this on every load instead of trusting anything it
    # stored, so the role always comes from the server.
    return current_user


@auth_router.patch("/me", response_model=ProfileOut)
def update_profile(new_info: ProfileUpdate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):

    current_user.name = new_info.name

    db.commit()
    db.refresh(current_user)

    return current_user


@auth_router.post("/me/password")
def change_password(body: PasswordChange, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):

    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=422,
            detail="Current password is wrong"
        )

    current_user.password_hash = hash_password(body.new_password)

    # Every token handed out before this moment now stops working, including
    # the one being used right now - so changing your password logs out the
    # laptop you left the session open on.
    current_user.token_version = current_user.token_version + 1

    db.commit()

    return {"message": "Password changed"}


@auth_router.get("/admin/users", response_model=list[UserOut])
def all_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):

    return db.query(User).filter(User.deleted_at.is_(None)).order_by(User.name).all()


@auth_router.patch("/users/{id}", response_model=UserOut)
def update_user(id: int, new_info: UserUpdate, db: Session = Depends(get_db),
                admin: User = Depends(require_admin)):

    user = db.query(User).filter(User.id == id, User.deleted_at.is_(None)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # exclude_unset, so "field not sent" and "field sent as null" stay
    # different things - otherwise every PATCH would blank the fields it did
    # not mention.
    data = new_info.model_dump(exclude_unset=True)

    # You cannot demote yourself. That also quietly protects the last admin:
    # with only one admin left, nobody else can reach this route at all.
    if user.id == admin.id and data.get("role") not in (None, user.role):
        raise HTTPException(
            status_code=409,
            detail="You cannot change your own role"
        )

    if "email" in data:
        email = data["email"].lower()
        taken = db.query(User).filter(User.email == email, User.id != user.id).first()

        if taken:
            raise HTTPException(status_code=409, detail="Email already registered")

        user.email = email
        data.pop("email")

    # Password is hashed, never written straight through like the other fields.
    if data.get("password"):
        user.password_hash = hash_password(data["password"])
        user.token_version = user.token_version + 1
    data.pop("password", None)

    for key, value in data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


@auth_router.delete("/users/{id}", response_model=UserOut)
def delete_user(id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):

    user = db.query(User).filter(User.id == id, User.deleted_at.is_(None)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(
            status_code=409,
            detail="You cannot remove your own account"
        )

    # Soft delete: the row stays, the login stops. get_current_user filters on
    # deleted_at, so an already-issued token stops working on the next request.
    user.deleted_at = now()

    db.commit()
    db.refresh(user)

    return user
