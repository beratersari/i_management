"""
Authentication endpoints:
  POST /auth/login          – OAuth2 password flow, returns access + refresh tokens
  POST /auth/refresh        – Exchange a valid refresh token for a new access token
  POST /auth/logout         – Revoke the provided refresh token
  POST /auth/logout-all     – Revoke all refresh tokens for the current user
  GET  /auth/me             – Return the currently authenticated user's profile
"""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
import logging

from backend.core.dependencies import db_dependency, get_current_active_user
from backend.models.user import User
from backend.schemas.token import Token, AccessToken, RefreshTokenRequest
from backend.schemas.user import UserResponse
from backend.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=Token,
    summary="Login with username/email and password (OAuth2 Password Flow)",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn=Depends(db_dependency),
):
    """
    Standard OAuth2 Password Flow endpoint.
    - **username**: your username *or* email address
    - **password**: your password

    Returns a short-lived **access token** (15 min) and a long-lived
    **refresh token** (7 days).
    """
    logger.info("Login requested for username=%s", form_data.username)
    service = AuthService(conn)
    return service.login(form_data.username, form_data.password)


@router.post(
    "/refresh",
    response_model=AccessToken,
    summary="Obtain a new access token using a valid refresh token",
)
def refresh_token(
    body: RefreshTokenRequest,
    conn=Depends(db_dependency),
):
    """
    Exchange a valid, non-revoked **refresh token** for a fresh **access token**.
    """
    logger.info("Refreshing access token")
    service = AuthService(conn)
    return service.refresh(body.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the provided refresh token",
)
def logout(
    body: RefreshTokenRequest,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """
    Revoke the supplied **refresh token**, effectively ending the session
    associated with that token.
    """
    logger.info("Logout requested")
    service = AuthService(conn)
    service.logout(body.refresh_token)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke all refresh tokens for the current user",
)
def logout_all(
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Revoke **every** refresh token issued to the currently authenticated user.
    Useful for "sign out everywhere" functionality.
    """
    logger.info("Logout all requested for user id=%s", current_user.id)
    service = AuthService(conn)
    service.logout_all(current_user.id)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user's profile",
)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Return the profile of the currently authenticated user."""
    logger.info("Returning profile for user id=%s", current_user.id)
    return current_user
