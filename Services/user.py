from typing import Annotated

from fastapi import HTTPException, status,Depends
from sqlalchemy.exc import IntegrityError
from config.hashing import hashPassword
from config.O2Auth import get_current_user
from Schemas.users import UserCreate
from Models.models import User
from sqlalchemy.orm import Session




from Schemas.users import UserBase


def register(user:UserCreate, db:Session):
    existing_user=db.query(User).filter(User.email==user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    hash=hashPassword(user.password)
    new_user=User(name=user.name,email=user.email,password=hash,role=user.role)
    db.add(new_user)
    try:
     db.commit()
     db.refresh(new_user)
     return new_user
    except IntegrityError:
     db.rollback()
     return {"error": "An unexpected error occurred. Please try again."}

def update(user:UserBase, db:Session, id:int, current_user:Annotated[User, Depends(get_current_user)]):
    if current_user.role !="customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action"
        )
    user_exists=db.query(User).filter(User.id==id).first()
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    update_data = {
        "name": user.name if user.name else getattr(user_exists, "name"),
        "email": user.email if user.email else getattr(user_exists, "email"),
        "role": user.role if user.role else getattr(user_exists , "role"),
    }
    db.query(User).filter(User.id == id).update(update_data)
    db.commit()
    db.refresh(user_exists)

    return user_exists


def get_all_users(db:Session,current_user:Annotated[User, Depends(get_current_user)]):

    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action"
        )
    return db.query(User).all()

def getUserById(db:Session, id:int):
    user= db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
def deleteUserById(db:Session, id:int):
    user= db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()
    return {'user': user,
            "message": 'User deleted successfully'}
