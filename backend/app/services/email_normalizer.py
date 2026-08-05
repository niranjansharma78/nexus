from __future__ import annotations

import quopri
import re
from html import unescape


def decode_quoted_printable(value: str) -> str:
    if not value:
        return ""

    text = value

    # Repair malformed quoted-printable word breaks such as:
    # "Mark= et" -> "Market"
    # "da= ted"  -> "dated"
    #
    # Do not modify valid hexadecimal encodings such as =3D or =20.
    text = re.sub(
        r"=(?![0-9A-Fa-f]{2})(?:\r?\n|\s+)(?=[A-Za-z0-9])",
        "",
        text,
    )

    try:
        return quopri.decodestring(
            text.encode("utf-8", errors="replace")
        ).decode("utf-8", errors="replace")
    except Exception:
        return text


def clean_email_text(value: str) -> str:
    text = decode_quoted_printable(value or "")
    text = re.sub(
        r"(?is)<(script|style|svg|canvas).*?>.*?</\1>",
        " ",
        text,
    )
    text = re.sub(r"(?is)<!--.*?-->", " ", text)
    text = re.sub(r"(?is)<!doctype.*?>", " ", text)
    text = re.sub(
        r"(?i)<br\s*/?>|</p>|</div>|</li>|</tr>|</h[1-6]>",
        "\n",
        text,
    )
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(
        r"(?im)^(content-type|content-transfer-encoding|mime-version):.*$",
        " ",
        text,
    )
    text = re.sub(
        r"(?m)^--[A-Za-z0-9_+=./?-]{8,}--?$",
        " ",
        text,
    )
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_summary(
    title: str | None,
    summary: str | None,
    category: str | None = None,
    entity_name: str | None = None,
    max_length: int = 420,
) -> str:
    cleaned = clean_email_text(summary or "")
    noisy = (
        "font-family",
        "media only screen",
        "mso-",
        "webkit-text-size-adjust",
        "xmlns:",
    )
    noise_score = sum(token in cleaned.lower() for token in noisy)

    if not cleaned or noise_score >= 2:
        subject = (title or "").strip()
        entity = (entity_name or "").strip()
        kind = (category or "email").replace("_", " ")

        if subject and subject != "(No subject)":
            cleaned = f"{subject}. {kind.title()} update received."
        elif entity:
            cleaned = f"{kind.title()} update received from {entity}."
        else:
            cleaned = f"{kind.title()} update received."

    return cleaned[:max_length].strip()
