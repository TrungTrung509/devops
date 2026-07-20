from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Optional

from configs.config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRES, REFRESH_TOKEN_EXPIRES, pwd_context
from configs.db import SessionLocals, get_db
from repositories.UserRepo import UserRepo
from schemas.Auth import Token, TokenData
from services.FailoverService import FailoverService

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
        return pwd_context.verify(plain_pwd, hashed_pwd)

    @staticmethod
    def get_password_hash(plain_pwd: str) -> str:
        return pwd_context.hash(plain_pwd)

    @staticmethod
    def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRES)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_tokens(user_data: dict) -> Token:
        access_token = AuthService.create_token(
            data=user_data,
            expires_delta=timedelta(minutes=TOKEN_EXPIRES)
        )
        refresh_token = AuthService.create_token(
            data={"sub": user_data.get("sub"), "type": "refresh"},
            expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRES)
        )
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    @staticmethod
    def verify_token(token: str) -> TokenData:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("userId")
            role: str = payload.get("role")
            branch_id: str = payload.get("branch_id")
            token_type: str = payload.get("type", "access")

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(username=username, userId=user_id, role=role, branch_id=branch_id)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def login(self, username: str, password: str) -> Token:
        user = UserRepo.get_by_username(self.db, username)
        if user is None:
            user = self._find_user_by_username(username)
        if not user or not self.verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return self.create_tokens({
            "sub": user.username,
            "userId": user.userId,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "branch_id": user.MaCoSo
        })

    async def refresh(self, refresh_token: str) -> Token:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                 raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
            
            username: str = payload.get("sub")
            user = UserRepo.get_by_username(self.db, username)
            if user is None:
                user = self._find_user_by_username(username)
            if user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
            
            return self.create_tokens({
                "sub": user.username,
                "userId": user.userId,
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "branch_id": user.MaCoSo
            })
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    async def logout(self, refresh_token: str):
        # Placeholder for blacklisting logic
        pass

    @staticmethod
    def _find_user_by_username(username: str):
        candidate_sites = []
        current_primary = FailoverService.get_current_primary_site(auto_failover=True)
        candidate_sites.append(current_primary)
        for site_id in SessionLocals:
            if site_id not in candidate_sites:
                candidate_sites.append(site_id)

        for site_id in candidate_sites:
            if not FailoverService.is_site_alive(site_id):
                continue
            db = SessionLocals[site_id]()
            try:
                user = UserRepo.get_by_username(db, username)
                if user is not None:
                    return user
            finally:
                db.close()
        return None

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)
