from pathlib import Path

from app.brain.runtime.service import BrainRuntime


def main() -> None:
    result = BrainRuntime(
        Path("data") / "nexus.db"
    ).run_cycle()

    print(result.to_dict())


if __name__ == "__main__":
    main()
