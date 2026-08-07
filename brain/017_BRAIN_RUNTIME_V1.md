# ADR-017: Brain Runtime v1

Status: Accepted  
Brain version: 1.0.0 Alpha 1

Brain Runtime coordinates one complete cognitive cycle:

1. Read persisted Universal Events.
2. Generate Curiosity Questions.
3. Write the Brain Journal.
4. Build shared Brain Context.
5. Generate the Executive Brief.
6. Return cycle health and errors.

## Design principles

- One failing engine must not crash the entire cycle.
- Every cycle returns observable results.
- Runtime orchestration remains separate from connectors.
- This milestone does not yet schedule itself continuously.
- This milestone does not yet convert legacy email evidence into Universal Events.
