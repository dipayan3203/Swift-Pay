from app.auth.jwt_handler import (
    create_access_token,
    verify_access_token,
)

token = create_access_token(
    {
        "merchant_id": 1,
        "email": "merchant@example.com",
    }
)

print("Token:\n")
print(token)

print("\nDecoded:\n")
print(verify_access_token(token))