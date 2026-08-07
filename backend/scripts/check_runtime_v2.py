from pathlib import Path

from app.brain.runtime_v2.service import CognitiveRuntimeV2


def main() -> None:
    result = CognitiveRuntimeV2(
        Path("data") / "nexus.db"
    ).run(
        trigger="manual",
        objective="Runtime v2 health check",
        world="system",
    )

    print(result.to_dict())


if __name__ == "__main__":
    main()
