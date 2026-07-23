from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

# In production, load these from your config or .env
from app.core.config import(
SECRET_KEY,
ALGORITHM,
ACCESS_TOKEN_EXPIRE_MINUTES,
)

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str):
    """
    Verify a JWT access token.
    Returns the decoded payload if valid.
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        return None