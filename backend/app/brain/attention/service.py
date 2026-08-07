from __future__ import annotations

from pathlib import Path

from .models import AttentionItem, AttentionPriority
from .repository import AttentionRepository


class AttentionEngine:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.repository = (
            AttentionRepository(database_path)
            if database_path is not None
            else None
        )

    def evaluate(self, item: AttentionItem) -> AttentionItem:
        score = (
            item.importance * 0.24
            + item.urgency * 0.22
            + item.risk * 0.20
            + item.relevance * 0.14
            + item.novelty * 0.10
            + item.confidence * 0.10
        )

        item.attention_score = round(max(0.0, min(score, 1.0)), 10)

        if item.attention_score >= 0.85:
            item.priority = AttentionPriority.CRITICAL
        elif item.attention_score >= 0.70:
            item.priority = AttentionPriority.HIGH
        elif item.attention_score >= 0.50:
            item.priority = AttentionPriority.MEDIUM
        elif item.attention_score >= 0.25:
            item.priority = AttentionPriority.LOW
        else:
            item.priority = AttentionPriority.DEFER

        item.should_escalate = (
            item.priority in {
                AttentionPriority.CRITICAL,
                AttentionPriority.HIGH,
            }
            and item.risk >= 0.60
        )
        item.should_process_now = (
            item.priority
            in {
                AttentionPriority.CRITICAL,
                AttentionPriority.HIGH,
            }
            or (
                item.priority == AttentionPriority.MEDIUM
                and item.urgency >= 0.75
            )
        )

        if self.repository is not None:
            self.repository.save(item)

        return item

    def rank(self, items: list[AttentionItem]) -> list[AttentionItem]:
        evaluated = [self.evaluate(item) for item in items]
        evaluated.sort(
            key=lambda item: (
                item.attention_score,
                item.urgency,
                item.risk,
            ),
            reverse=True,
        )
        return evaluated
