from __future__ import annotations

import email
import imaplib
import re
import socket
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.message import Message
from email.policy import default
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

from app.services.email_intelligence import interpret_email


imaplib._MAXLINE = 10_000_000


@dataclass(slots=True)
class IMAPSettings:
    host: str
    port: int
    username: str
    password: str
    folder: str = "INBOX"
    use_ssl: bool = True
    timeout_seconds: int = 30


@dataclass(slots=True)
class EmailAttachment:
    filename: str
    content_type: str
    payload: bytes


@dataclass(slots=True)
class EmailEvidence:
    source: str
    title: str
    summary: str
    domain: str
    occurred_at: str
    confidence: float
    status: str
    entity_name: str | None
    requires_decision: int
    priority: int
    message_id: str | None
    sender: str | None
    attachments: list[EmailAttachment] = field(default_factory=list)


class IMAPSensorError(RuntimeError):
    pass


class IMAPSensor:
    """Read-only IMAP sensor with attachment capture."""

    def __init__(self, settings: IMAPSettings):
        self.settings = settings

    def _connect(self):
        socket.setdefaulttimeout(self.settings.timeout_seconds)

        try:
            client = (
                imaplib.IMAP4_SSL(
                    self.settings.host,
                    self.settings.port,
                    timeout=self.settings.timeout_seconds,
                )
                if self.settings.use_ssl
                else imaplib.IMAP4(
                    self.settings.host,
                    self.settings.port,
                    timeout=self.settings.timeout_seconds,
                )
            )

            client.login(self.settings.username, self.settings.password)

            status, _ = client.select(
                self.settings.folder,
                readonly=True,
            )

            if status != "OK":
                self._safe_close(client)
                raise IMAPSensorError(
                    f"Could not open folder {self.settings.folder!r}"
                )

            return client

        except (imaplib.IMAP4.error, OSError, TimeoutError) as exc:
            raise IMAPSensorError(str(exc)) from exc

    def test_connection(self) -> dict:
        client = self._connect()

        try:
            status, data = client.status(
                self.settings.folder,
                "(MESSAGES UNSEEN)",
            )

            return {
                "ok": status == "OK",
                "folder": self.settings.folder,
                "status": (
                    data[0].decode(errors="replace")
                    if data
                    else ""
                ),
            }

        finally:
            self._safe_close(client)

    def scan_recent(self, limit: int = 50) -> list[EmailEvidence]:
        client = self._connect()

        try:
            since_date = (
                datetime.now() - timedelta(days=365)
            ).strftime("%d-%b-%Y")

            status, data = client.uid(
                "search",
                None,
                "SINCE",
                since_date,
            )

            if status != "OK":
                raise IMAPSensorError("Mailbox search failed")

            all_uids = data[0].split() if data and data[0] else []
            selected = all_uids[-max(1, min(limit, 500)):]

            results: list[EmailEvidence] = []

            for uid in reversed(selected):
                status, payload = client.uid(
                    "fetch",
                    uid,
                    "(BODY.PEEK[])",
                )

                if status != "OK":
                    continue

                raw = _combine_fetch_payload(payload)
                if not raw:
                    continue

                message = email.message_from_bytes(
                    raw,
                    policy=default,
                )

                results.append(_to_evidence(message))

            return results

        except (imaplib.IMAP4.error, OSError, TimeoutError) as exc:
            raise IMAPSensorError(str(exc)) from exc

        finally:
            self._safe_close(client)

    @staticmethod
    def _safe_close(client) -> None:
        try:
            client.close()
        except Exception:
            pass

        try:
            client.logout()
        except Exception:
            pass


def _combine_fetch_payload(payload) -> bytes:
    chunks: list[bytes] = []

    for item in payload or []:
        if isinstance(item, tuple) and isinstance(item[1], bytes):
            chunks.append(item[1])

    return b"\r\n".join(chunks)


def _decoded(value: str | None) -> str:
    if not value:
        return ""

    try:
        return str(make_header(decode_header(value))).strip()
    except Exception:
        return value.strip()


def _decode_part(part: Message) -> str:
    try:
        content = part.get_content()
        if isinstance(content, str):
            return content
    except Exception:
        pass

    payload = part.get_payload(decode=True)
    if not payload:
        return ""

    charset = part.get_content_charset() or "utf-8"

    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _html_to_text(value: str) -> str:
    text = re.sub(
        r"(?is)<(script|style).*?>.*?</\1>",
        " ",
        value,
    )
    text = re.sub(r"(?is)<!--.*?-->", " ", text)
    text = re.sub(
        r"(?i)<br\s*/?>|</p>|</div>|</li>|</tr>|</h[1-6]>",
        "\n",
        text,
    )
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _plain_text(message: Message) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
                continue

            disposition = (
                part.get_content_disposition()
                or ""
            ).lower()

            if disposition == "attachment":
                continue

            content_type = part.get_content_type()
            decoded = _decode_part(part)

            if not decoded:
                continue

            if content_type == "text/plain":
                plain_parts.append(decoded)
            elif content_type == "text/html":
                html_parts.append(decoded)

        if plain_parts:
            return "\n".join(plain_parts)

        if html_parts:
            return _html_to_text("\n".join(html_parts))

        return ""

    decoded = _decode_part(message)

    if message.get_content_type() == "text/html":
        return _html_to_text(decoded)

    return decoded


def _attachments(message: Message) -> list[EmailAttachment]:
    results: list[EmailAttachment] = []

    for index, part in enumerate(message.walk(), start=1):
        if part.is_multipart():
            continue

        disposition = (
            part.get_content_disposition()
            or ""
        ).lower()
        filename = _decoded(part.get_filename())

        if disposition != "attachment" and not filename:
            continue

        payload = part.get_payload(decode=True)
        if not payload:
            continue

        if not filename:
            extension = Path(
                part.get_content_type().replace("/", ".")
            ).suffix
            filename = f"attachment_{index}{extension}"

        results.append(
            EmailAttachment(
                filename=filename,
                content_type=part.get_content_type(),
                payload=payload,
            )
        )

    return results


def _clean_body(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"(?is)<!DOCTYPE.*?>", " ", text)
    text = re.sub(r"(?is)<html.*?>|</html>", " ", text)
    text = re.sub(r"(?im)^content-type:.*$", " ", text)
    text = re.sub(
        r"(?im)^content-transfer-encoding:.*$",
        " ",
        text,
    )
    text = re.sub(
        r"(?m)^--[A-Za-z0-9_+=./?-]{8,}--?$",
        " ",
        text,
    )
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_date(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()

    try:
        parsed = parsedate_to_datetime(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.isoformat()

    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _to_evidence(message: Message) -> EmailEvidence:
    subject = _decoded(message.get("Subject")) or "(No subject)"
    sender = _decoded(message.get("From"))
    body = _clean_body(_plain_text(message))

    interpretation = interpret_email(
        subject=subject,
        body=body,
        sender=sender,
    )

    return EmailEvidence(
        source="IMAP",
        title=subject,
        summary=interpretation.clean_summary,
        domain=interpretation.domain,
        occurred_at=_parse_date(message.get("Date")),
        confidence=interpretation.confidence,
        status="recorded",
        entity_name=interpretation.entity_name,
        requires_decision=interpretation.requires_decision,
        priority=interpretation.priority,
        message_id=_decoded(message.get("Message-ID")) or None,
        sender=sender or None,
        attachments=_attachments(message),
    )
