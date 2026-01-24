"""Kalshi request signing and config-from-env helpers.

Uses the cryptography and python-dotenv packages (core dependencies).
"""

from __future__ import annotations

import base64
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from kyro.exceptions import KyroError

if TYPE_CHECKING:
    from kyro._config import KyroConfig


def _load_private_key(pem_or_path: str | bytes) -> Any:
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
    except ImportError as e:
        raise KyroError(
            "cryptography is required for Kalshi request signing; reinstall kyro"
        ) from e

    if isinstance(pem_or_path, bytes):
        pem = pem_or_path
    else:
        s = pem_or_path.strip()
        if s.startswith("-----"):
            pem = s.replace("\\n", "\n").encode("utf-8")
        else:
            pem = Path(s).expanduser().read_bytes()
    return load_pem_private_key(pem, password=None)


def _create_signer(
    key_id: str, private_key: Any
) -> Callable[[str, str, bytes | None], dict[str, str]]:
    def sign(method: str, path: str, body: bytes | None) -> dict[str, str]:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        path_clean = path.split("?")[0]
        ts = str(int(time.time() * 1000))
        message = (ts + method + path_clean).encode("utf-8")
        signature = private_key.sign(
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256(),
        )
        return {
            "KALSHI-ACCESS-KEY": key_id,
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("utf-8"),
        }

    return sign


def config_from_env(*, default_demo: bool = False) -> KyroConfig:
    """Build :class:`KyroConfig` from environment variables.

    Loads a ``.env`` file from the current directory when ``python-dotenv`` is available
    (python-dotenv is a core dependency). You can put ``KALSHI_*`` there instead of exporting.

    **URL / environment:**
    - ``KALSHI_BASE_URL`` — override base URL (e.g. ``https://demo-api.kalshi.co/trade-api/v2``).
    - ``KALSHI_DEMO=1`` — use demo base URL when ``KALSHI_BASE_URL`` is not set.
    - ``KALSHI_PRODUCTION=1`` — use production base URL when ``KALSHI_BASE_URL`` is not set.
    - If none are set: use demo when ``default_demo=True``, else production.

    **Auth (Kalshi RSA-PSS signing):**
    - ``KALSHI_ACCESS_KEY`` or ``KALSHI_ACCESS_KEY_ID`` — API key ID.
    - ``KALSHI_PRIVATE_KEY`` — PEM string (use ``\\n`` for newlines in env).
    - ``KALSHI_PRIVATE_KEY_PATH`` — path to a ``.key`` or ``.pem`` file (used when ``KALSHI_PRIVATE_KEY`` is not set).

    When both key ID and private key are present, request signing is enabled and auth-required
    endpoints will work. Uses the ``cryptography`` package (core dependency).
    """
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    from kyro._config import KyroConfig

    base_url = os.environ.get("KALSHI_BASE_URL", "").strip() or None
    if not base_url:
        demo = os.environ.get("KALSHI_DEMO", "").strip().lower() in ("1", "true", "yes")
        prod = os.environ.get("KALSHI_PRODUCTION", "").strip().lower() in ("1", "true", "yes")
        if demo:
            base_url = "https://demo-api.kalshi.co/trade-api/v2"
        elif prod:
            base_url = "https://api.elections.kalshi.com/trade-api/v2"
        elif default_demo:
            base_url = "https://demo-api.kalshi.co/trade-api/v2"
        else:
            base_url = "https://api.elections.kalshi.com/trade-api/v2"

    key_id = os.environ.get("KALSHI_ACCESS_KEY") or os.environ.get("KALSHI_ACCESS_KEY_ID") or ""
    key_id = key_id.strip()
    pem_val = os.environ.get("KALSHI_PRIVATE_KEY", "").strip()
    pem_path = os.environ.get("KALSHI_PRIVATE_KEY_PATH", "").strip()

    auth_signer = None
    if key_id and (pem_val or pem_path):
        raw = pem_val if pem_val else pem_path
        key = _load_private_key(raw)
        auth_signer = _create_signer(key_id, key)

    return KyroConfig(base_url=base_url, auth_signer=auth_signer)
