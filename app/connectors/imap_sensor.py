from __future__ import annotations

import email
import imaplib
import re
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable
from app.services.email_intelligence import interpret_email


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


class IMAPSensorError(RuntimeError):
    pass


class IMAPSensor:
    """Read-only IMAP sensor.

    The sensor uses SELECT readonly=True and only FETCH operations.
    It never sends STORE, COPY, MOVE, DELETE, EXPUNGE or APPEND commands.
    """

    def __init__(self, settings: IMAPSettings):
        self.settings = settings

    def _connect(self):
        socket.setdefaulttimeout(self.settings.timeout_seconds)
        try:
            if self.settings.use_ssl:
                client = imaplib.IMAP4_SSL(
                    self.settings.host,
                    self.settings.port,
                    timeout=self.settings.timeout_seconds,
                )
            else:
                client = imaplib.IMAP4(
                    self.settings.host,
                    self.settings.port,
                    timeout=self.settings.timeout_seconds,
                )
            client.login(self.settings.username, self.settings.password)
            status, _ = client.select(self.settings.folder, readonly=True)
            if status != "OK":
                client.logout()
                raise IMAPSensorError(f"Could not open folder {self.settings.folder!r}")
            return client
        except (imaplib.IMAP4.error, OSError, TimeoutError) as exc:
            raise IMAPSensorError(str(exc)) from exc

    def test_connection(self) -> dict:
        client = self._connect()
        try:
            status, data = client.status(self.settings.folder, "(MESSAGES UNSEEN)")
            return {
                "ok": status == "OK",
                "folder": self.settings.folder,
                "status": data[0].decode(errors="replace") if data else "",
            }
        finally:
            try:
                client.close()
            except Exception:
                pass
            client.logout()

    def scan_recent(self, limit: int = 50) -> list[EmailEvidence]:
        client = self._connect()
        try:
            status, data = client.uid("search", None, "ALL")
            if status != "OK":
                raise IMAPSensorError("Mailbox search failed")

            all_uids = data[0].split()
            selected = all_uids[-max(1, min(limit, 500)):]
            results: list[EmailEvidence] = []

            for uid in reversed(selected):
                status, payload = client.uid(
                    "fetch",
                    uid,
                    "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)] BODY.PEEK[TEXT])",
                )
                if status != "OK":
                    continue

                raw = _combine_fetch_payload(payload)
                if not raw:
                    continue

                message = email.message_from_bytes(raw)
                results.append(_to_evidence(message))

            return results
        finally:
            try:
                client.close()
            except Exception:
                pass
            client.logout()


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


def _plain_text(message: Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disposition:
                continue
            if content_type == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8",
                        errors="replace",
                    )
                except Exception:
                    continue
        for part in message.walk():
            if part.get_content_type() == "text/html":
                try:
                    html = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8",
                        errors="replace",
                    )
                    return re.sub(r"<[^>]+>", " ", unescape(html))
                except Exception:
                    continue
        return ""

    payload = message.get_payload(decode=True)
    if not payload:
        return ""
    text = payload.decode(message.get_content_charset() or "utf-8", errors="replace")
    if message.get_content_type() == "text/html":
        text = re.sub(r"<[^>]+>", " ", unescape(text))
    return text


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

    body = re.sub(r"\s+", " ", _plain_text(message)).strip()

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
    )
   
