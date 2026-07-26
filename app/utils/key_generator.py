import secrets
import string


ALPHABET = string.ascii_letters + string.digits


def _random_string(length: int = 32) -> str:
    return "".join(
        secrets.choice(ALPHABET)
        for _ in range(length)
    )


def generate_public_key(environment: str = "TEST") -> str:
    """
    Generates:
    pk_test_xxxxxxxxxxxxx
    pk_live_xxxxxxxxxxxxx
    """

    prefix = (
        "pk_test_"
        if environment.upper() == "TEST"
        else "pk_live_"
    )

    return prefix + _random_string(32)


def generate_secret_key(environment: str = "TEST") -> str:
    """
    Generates:
    sk_test_xxxxxxxxxxxxx
    sk_live_xxxxxxxxxxxxx
    """

    prefix = (
        "sk_test_"
        if environment.upper() == "TEST"
        else "sk_live_"
    )

    return prefix + _random_string(48)