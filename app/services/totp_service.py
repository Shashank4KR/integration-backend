import base64
import hmac
import secrets
import struct
import time
import urllib.parse


class TOTPService:
    """RFC 6238 compliant Time-Based One-Time Password (TOTP) service.

    Implemented using Python standard library without external dependencies.
    Compatible with Google Authenticator, Authy, 1Password, etc.
    """

    INTERVAL: int = 30
    DIGITS: int = 6

    @classmethod
    def generate_secret(cls) -> str:
        """Generate a cryptographically secure 160-bit base32 secret."""
        return base64.b32encode(secrets.token_bytes(20)).decode("utf-8")

    @classmethod
    def get_provisioning_uri(
        cls, account_name: str, secret: str, issuer: str = "EdTech"
    ) -> str:
        """Generate standard otpauth:// URL for QR code generation."""
        encoded_account = urllib.parse.quote(account_name)
        encoded_issuer = urllib.parse.quote(issuer)
        return (
            f"otpauth://totp/{encoded_issuer}:{encoded_account}"
            f"?secret={secret}&issuer={encoded_issuer}&algorithm=SHA1&digits={cls.DIGITS}&period={cls.INTERVAL}"
        )

    @classmethod
    def generate_totp(
        cls, secret: str, for_time: float | None = None
    ) -> str:
        """Compute the 6-digit TOTP code for the given time."""
        if for_time is None:
            for_time = time.time()
        counter = int(for_time // cls.INTERVAL)
        key = base64.b32decode(secret, casefold=True)
        msg = struct.pack(">Q", counter)
        h = hmac.new(key, msg, "sha1").digest()
        offset = h[-1] & 0x0F
        binary_code = (
            struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF
        )
        code = binary_code % (10**cls.DIGITS)
        return str(code).zfill(cls.DIGITS)

    @classmethod
    def verify_totp(
        cls, secret: str, code: str, window: int = 1
    ) -> bool:
        """Verify code against secret with a skew tolerance of +/- `window` intervals (default +/- 30s)."""
        if not secret or not code or len(code.strip()) != cls.DIGITS:
            return False
        clean_code = code.strip()
        now = time.time()
        for offset in range(-window, window + 1):
            if (
                cls.generate_totp(
                    secret, for_time=now + offset * cls.INTERVAL
                )
                == clean_code
            ):
                return True
        return False
