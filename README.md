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

## Install

```bash
uv pip install testprotocols testoperations
```

Both packages are on PyPI and release in lockstep; pin
`testprotocols>=0.M.P,<0.(M+1).0` and the same for `testoperations`.
The per-domain protocol design references are under `docs/architecture/`;
the consumer-side development flow is documented in the consumer
repositories.

## Contributing

Changes to the contracts start as a proposal; see
[`docs/proposals/README.md`](docs/proposals/README.md). Everything else,
from PR kinds to the release procedure, is in
[`CONTRIBUTING.md`](CONTRIBUTING.md). Questions go in an issue with the
`question` label.

<!-- hygiene check -->
