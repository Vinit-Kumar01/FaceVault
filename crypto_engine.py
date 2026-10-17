
import os
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken


def _get_cipher(password: str, salt: bytes) -> Fernet:
    key_bytes = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(key)


def encrypt_file(input_path: str, password: str) -> str:
    source = Path(input_path)

    if not source.is_file():
        raise FileNotFoundError(f"File not found: {source}")

    if not password:
        raise ValueError("Password cannot be empty.")

    salt = os.urandom(16)
    cipher = _get_cipher(password, salt)

    original_data = source.read_bytes()
    encrypted_data = cipher.encrypt(original_data)

    output_path = source.with_name(source.name + ".vault")
    output_path.write_bytes(b"FV1" + salt + encrypted_data)

    return str(output_path)


def decrypt_file(input_path: str, password: str) -> str:
    source = Path(input_path)
    stored_data = source.read_bytes()

    if not stored_data.startswith(b"FV1") or len(stored_data) < 20:
        raise ValueError("This is not a valid FaceVault encrypted file.")

    salt = stored_data[3:19]
    encrypted_data = stored_data[19:]
    cipher = _get_cipher(password, salt)

    try:
        original_data = cipher.decrypt(encrypted_data)
    except InvalidToken:
        raise ValueError("Wrong password or damaged encrypted file.") from None

    if source.name.endswith(".vault"):
        original_name = source.name[:-len(".vault")]
        output_path = source.with_name(original_name)
    else:
        output_path = source.with_name(source.name + ".restored")

    if output_path.exists():
        raise FileExistsError(
            "You already have your original file!\n\n"
            f"File location:\n{output_path}\n\n"
            "No new file was created."
        )

    output_path.write_bytes(original_data)
    return str(output_path)
