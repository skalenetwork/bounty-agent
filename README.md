![Test](https://github.com/skalenetwork/bounty-agent/workflows/Test/badge.svg)
![Build and publish](https://github.com/skalenetwork/bounty-agent/workflows/Build%20and%20publish/badge.svg)
[![codecov](https://codecov.io/gh/skalenetwork/bounty-agent/branch/develop/graph/badge.svg)](https://codecov.io/gh/skalenetwork/bounty-agent)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/84747976cadf49958eacbb48e7597f08)](https://www.codacy.com/gh/skalenetwork/bounty-agent?utm_source=github.com\&utm_medium=referral\&utm_content=skalenetwork/bounty-agent\&utm_campaign=Badge_Grade)
[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

# SKALE Bounty Agent

SKALE Bounty Agent is a part of each SKALE Node, and together is part of the SKALE Node Monitoring Service (NMS).
Every SKALE node has a NMS group of N (e.g. 24) other nodes in the network randomly assigned to it. NMS groups regularly audit various node metrics at predetermined periods (e.g. five minutes), log these measurements to their local databases, and submit average metrics to the SKALE Manager Contract (SMC) once for every reward period - epoch (e.g. 30 days).

Every node is rewarded for its validation efforts, based on results sent by NMS group of this node, at the end of each epoch.
Bounty agent runs on every node of SKALE network, periodically requests available bounties for validation work from the SMC(once for every epoch).

## An important note about production readiness

Bounty Agent is still in active development and therefore should be regarded as alpha software. The development is still subject to security hardening, further testing, and breaking changes. This repository has not yet been reviewed or audited for security.

## Development

### Requirements

Python ≥ 3.13

### Dependencies

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install all dependencies:

```bash
uv sync --prerelease=allow --all-extras
```

### Linting and type checking

#### Check linting/formatting issues

```bash
uv run ruff check
```

#### Check type issues

```bash
uv run mypy .
```

### Run tests locally

1. Export environment variables:

```bash
. ./scripts/export_env.sh
```

2. Deploy skale-manager:

```bash
bash helper-scripts/deploy_manager.sh
```

3. Run tests:

```bash
bash ./scripts/run_tests.sh
```

### Build

For building Bounty agent docker image locally:

```bash
docker build -t your-bounty-image-name .
```

## For more information

* [SKALE Network Website](https://skale.space)
* [SKALE Network Twitter](https://twitter.com/SkaleNetwork)
* [SKALE Network Blog](https://skale.space/blog)

Learn more about the SKALE community over on [Discord](http://skale.chat).

## Contributing

**If you have any questions please ask our development community on [Discord](https://discord.gg/vvUtWJB).**
[![Discord](https://img.shields.io/discord/534485763354787851.svg)](https://discord.gg/vvUtWJB)

## License

[![License](https://img.shields.io/github/license/skalenetwork/bounty-agent)](LICENSE)
Copyright (C) 2018-present SKALE Labs
