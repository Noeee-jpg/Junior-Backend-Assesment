import secrets

secret_key = secrets.token_hex(32)  # Generates a random key of 64 characters (32 bytes)
print(secret_key)
