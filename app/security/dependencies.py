from fastapi import Depends, HTTPException, status

from configs.config import oauth2_scheme
from configs.db import SessionLocals
from enums.status import UserStatus
from enums.user_role import UserRole
from models.Users import User
from repositories.UserRepo import UserRepo
from services.AuthService import AuthService
from services.FailoverService import FailoverService


def _role_to_string(role: UserRole | str) -> str:
    return role.value if hasattr(role, "value") else str(role)


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    token_data = AuthService.verify_token(token)
    site = (token_data.branch_id or "HADONG").upper()

    candidate_sites = []
    if site in SessionLocals:
        candidate_sites.append(site)
    current_primary = FailoverService.get_current_primary_site(auto_failover=True)
    if current_primary not in candidate_sites:
        candidate_sites.append(current_primary)
    for candidate in SessionLocals:
        if candidate not in candidate_sites:
            candidate_sites.append(candidate)

    for candidate in candidate_sites:
        if not FailoverService.is_site_alive(candidate):
            continue
        db = SessionLocals[candidate]()
        try:
            user = UserRepo.get_by_username(db, token_data.username)
            if user is not None:
                return user
        finally:
            db.close()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.status != UserStatus.Active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


def get_current_user_db(current_user: User = Depends(get_current_active_user)):
    db = FailoverService.open_read_session(
        preferred_site=current_user.MaCoSo,
        auto_failover=True,
    )
    try:
        yield db
    finally:
        db.close()


def require_roles(*roles: UserRole):
    allowed_roles = {_role_to_string(role) for role in roles}

    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        current_role = _role_to_string(current_user.role)
        if current_role not in allowed_roles:
            allowed = ", ".join(sorted(allowed_roles))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {allowed}",
            )
        return current_user

    return dependency
