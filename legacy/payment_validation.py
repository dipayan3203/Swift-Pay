from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.database.storage import Storage

ALLOWED_CURRENCIES = {"INR", "USD", "EUR"}
ALLOWED_METHODS = {"card", "upi", "wallet"}

def validate_payment(storage: 'Storage', payload: dict, require_merchant: bool = True):
    amount_minor = payload.get("amount_minor")
    if not isinstance(amount_minor, int) or amount_minor <= 0:
        return False, "amount_minor must be a positive integer"
    if payload.get("currency") not in ALLOWED_CURRENCIES:
        return False, f"currency must be one of {sorted(ALLOWED_CURRENCIES)}"
    if payload.get("payment_method") not in ALLOWED_METHODS:
        return False, f"payment_method must be one of {sorted(ALLOWED_METHODS)}"
    merchant_id = payload.get("merchant_id")
    if require_merchant and not merchant_id:
        return False, "merchant_id is required"
    if merchant_id and not storage.find("merchants", merchant_id):
        return False, "merchant_id not found"
    return True, None