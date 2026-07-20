from sqlalchemy.orm import Session
from models.Users import User

class UserRepo:
    @staticmethod
    def get_by_username(db: Session, username: str) -> User:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_by_id(db: Session, userId: str) -> User:
        return db.query(User).filter(User.userId == userId).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> User:
        if not email: return None
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User) -> User:
        db.commit()
        db.refresh(user)
        return user
