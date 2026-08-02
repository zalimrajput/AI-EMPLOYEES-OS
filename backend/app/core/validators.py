def validate_password(password: str):

    if len(password) < 8:
        raise ValueError(
            "Password must be at least 8 characters"
        )

    if len(password.encode("utf-8")) > 72:
        raise ValueError(
            "Password cannot exceed 72 bytes"
        )

    if password.islower() or password.isupper() or password.isdigit():
        raise ValueError(
            "Password must contain uppercase, lowercase and numbers"
        )

    return True