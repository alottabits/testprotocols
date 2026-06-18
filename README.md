# testprotocols — Common Test Resource Layer (CTRL)

Framework-neutral test interface for telco resources. Two sibling Python packages:

- **`testprotocols`** — capability and device contracts as `typing.Protocol`s, plus the dataclass models they refer to.
- **`testoperations`** — assertion-free composition functions over capability protocols.

Both packages are stdlib-only (and inter-package imports). No dependency on
`palco`, `pytest`, `robot`, or any other framework — adopt them under any test
harness, or even outside testing entirely (inventory tools, CLI utilities).

## Layout

```
testprotocols/
├── packages/
│   ├── testprotocols/            (Python package: protocols + models)
│   │   ├── pyproject.toml
│   │   ├── src/testprotocols/
│   │   │   ├── *.py              (capability protocols)
│   │   │   ├── devices/*.py      (device archetype protocols)
│   │   │   └── models/*.py       (dataclass models)
│   │   └── tests/
│   └── testoperations/           (Python package: framing)
│       ├── pyproject.toml
│       ├── src/testoperations/
│       │   └── *.py
│       └── tests/
├── docs/
│   └── architecture/             (protocol design references)
└── pyproject.toml                (root: dev tooling only)
```

## Adopt under palco

```bash
uv pip install -e packages/testprotocols
uv pip install -e packages/testoperations
```

See the per-domain protocol design references under `docs/architecture/`
and the consumer architecture spec in
[palco-bdd/docs/architecture/palco-architecture.md](https://github.com/alottabits/palco-bdd/blob/main/docs/architecture/palco-architecture.md).
