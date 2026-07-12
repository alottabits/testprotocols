# testprotocols — Common Test Resource Layer (CTRL)

Framework-neutral test interface for telco resources. Two sibling Python packages:

- **`testprotocols`** — capability and device contracts as `typing.Protocol`s, plus the dataclass models they refer to.
- **`testoperations`** — assertion-free composition functions over capability
  protocols: throughput measurement, segmentation, criteria-driven candidate
  selection, poll-until-converge waiting, homing, and friends — mechanics only,
  verdicts stay with the caller.

Both packages are stdlib-only (and inter-package imports). No dependency on
`vitro`, `pytest`, `robot`, or any other framework — adopt them under any test
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
│       │   └── *.py              (per-domain operation modules)
│       └── tests/
├── docs/
│   └── architecture/             (protocol design references)
└── pyproject.toml                (root: dev tooling only)
```

## Adopt under vitro

```bash
uv pip install -e packages/testprotocols
uv pip install -e packages/testoperations
```

See the per-domain protocol design references under `docs/architecture/`
and the consumer architecture docs in
[vitro-bdd](https://github.com/alottabits/vitro-bdd)
(`docs/architecture/architecture-overview.md`).
