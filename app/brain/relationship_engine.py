from collections import defaultdict

def build_relationship_snapshots(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        entity = (row.get("entity_name") or "").strip()
        if entity:
            grouped[entity].append(row)

    result = []
    for entity, items in grouped.items():
        positive = sum(1 for x in items if x.get("relationship_impact") == "positive")
        negative = sum(1 for x in items if x.get("relationship_impact") == "negative")
        neutral = len(items) - positive - negative
        score = max(0, min(100, 70 + positive * 6 - negative * 9 + min(neutral, 5)))
        direction = "declining" if negative >= positive + 2 else "improving" if positive >= negative + 2 else "stable"
        result.append({
            "entity_name": entity,
            "score": score,
            "direction": direction,
            "evidence_count": len(items),
            "positive_count": positive,
            "negative_count": negative,
            "last_seen_at": max((str(x.get("occurred_at") or "") for x in items), default=None),
        })
    return sorted(result, key=lambda x: (x["direction"] == "declining", x["evidence_count"]), reverse=True)
