# Contributing to newton-usd-schemas

If you are interested in contributing to newton-usd-schemas, your contributions will fall
into three categories:
1. You want to report a bug, feature request, or documentation issue
2. You want to implement a feature or bug-fix for an outstanding issue
3. You want to propose a new Feature and implement it

In all cases, first search the existing [GitHub Issues](https://github.com/newton-physics/newton-usd-schemas/issues) to see if anyone has reported something similar.

If not, create a new [GitHub Issue](https://github.com/newton-physics/newton-usd-schemas/issues/new/choose) describing what you encountered or what you want to see changed. If you have feedback that is best explained in code, feel free to fork the repository on GitHub, create a branch demonstrating your intent, and either link it to the GitHub Issue or open a Pull Request back upstream. See [Code Contributions](#code-contributions) for more details.

Whether adding details to an existing issue or creating a new one, please let us know what companies are impacted.

## Code contributions

If you want to implement a feature, or change the logic of existing features, you are welcome to modify the code on a personal clone/mirror/fork. See [Building](#building) for more details.

If you want to contribute your changes back upstream, please first start a GitHub Issue as described above.

If you intend to submit a Pull Request:
- First, ensure alignment with the Code Owners on the associated Issue, to avoid redundant work or wasted iterations.
- Develop your changes on a well named [development branch](#development-branches) within your personal clone/mirror/fork.
- Run all test suites locally and ensure passing results in your dev environment.
- Add or update tests that are as thorough as the existing test suites, as described in [Test Requirements](#test-requirements).
- Add changelog entries as described in [Changelog](#changelog).
- Fill in the [PR template](.github/PULL_REQUEST_TEMPLATE.md), including its checklist. When opening the PR with `gh pr create --body` or `--fill`, the template is not applied automatically, so copy it into the body.
- Be prepared to sign the Newton Contributor License Agreement, see below.

Please note that in some cases, we may not merge GitHub Pull Requests directly. We will take suggestions under advisement and discuss internally. We may rebase your commits to provide alignment with internal development branches.

### Contributor License Agreement

All contributions to this project require a signed Contributor License Agreement (CLA) on file, see [Legal Requirements](https://github.com/newton-physics/newton-governance/blob/main/CONTRIBUTING.md#legal-requirements) in the Newton contribution guidelines.

Newton repositories use [EasyCLA](https://lfcla.com/) for managing CLAs. You may sign the appropriate CLA in a pull-request workflow; see [the EasyCLA documentation](https://docs.linuxfoundation.org/lfx/easycla/v2-current/contributors) for instructions.

### Branches and Versions

The default branch is named `main` and it is a protected branch. Our CI Pipeline automatically builds and tests all changes from this branch on both Windows and Linux. However, all new features target the `main` branch, and we may merge code changes to this branch at any time; it is not guaranteed to be stable/usable and may break API/ABI regularly.

We advise to use an official published wheel of the newton-usd-schemas, or source from the GitHub tag associated with it, to ensure stability.

### Development Branches

For all development, changes are pushed into a branch in personal development forks, and code is submitted upstream for code review and CI verification before being merged into `main` or the target release branch.

We do not enforce any particular naming convention for development branches, other than avoiding the reserved branch patterns `main` and `production/*`. We recommend using legible branch names that imply the feature or fix being developed.

All code changes must contain either new unittests, or updates to existing tests, and we won't merge any code changes that have failing CI pipelines or sub-standard code coverage.

## Changelog

Each PR adds its changelog entries to `CHANGELOG.md` under an `# Unreleased` heading at the top of the file. Create the heading if it does not exist. Do not add a version heading or bump the version; that happens during [release preparation](#release-preparation).

Entries must match the voice of the existing changelog. Read the most recent releases before writing yours:

- File entries under `## Features`, `## Fixes`, `## Documentation`, or `## Breaking Changes`.
- Wrap schema, attribute, token, and prim type names in backticks.
- Use nested bullets for consequences, caveats, and migration notes that users need. Leave implementation details to the PR description.

Skip the entry only for changes that fit none of those sections, such as test-only changes or internal refactors, and say so in the PR description.

### Release Preparation

The release preparation PR renames `# Unreleased` to the new version. Before it does, it reviews every commit merged since the previous release tag and backfills entries for changes that were missed during review. It may also reword entries in that release for a consistent voice, or merge related entries so the release reads as one coherent story. Unreleased entries are not final until the release ships.

## Developing

This project uses [uv](https://docs.astral.sh/uv/) as the primary dev tool and [poethepoet](https://github.com/nat-n/poethepoet) for command automation.

If you do not have `uv` installed, see the [development requirements](#development-requirements).

### Quick Start

Once `uv` is installed, you can use the following commands:

```bash
# Build the project
uv build

# Run linting
uv run --group dev poe lint

# Run tests
uv run --group dev poe test
```

The `dev` group includes an OpenUSD runtime and `usd-validation-nvidia`, through the extras defined in `pyproject.toml`.

### Development Requirements

To use the build scripts locally, you need uv installed:

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Common Commands

- Update dependencies: Edit `pyproject.toml` and then run `uv lock`
- Build the sdist and wheel: `uv build`
- Build just the wheel: `uv build --wheel`
- Run linting: `uv run --group dev poe lint`
- Run tests: `uv run --group dev poe test`
- Run auto-formatters: `uv run --group dev poe format`

### Validation Requirements

The requirements implemented by the validators are specified by pages in [`docs/specs/requirements`](docs/specs/requirements), and grouped by schema into capabilities by pages in [`docs/specs/capabilities`](docs/specs/capabilities). A new validator needs a new requirement page, with valid and invalid examples, which the tests validate.

The `newton_simulation` feature in [`docs/specs/features`](docs/specs/features) lists the requirements that content needs for Newton, including requirements from other packages, and the `Newton-Simulation` profile in [`docs/specs/profiles/profiles.toml`](docs/specs/profiles/profiles.toml) selects it. Add a new requirement to the feature when Newton relies on it, and bump the feature and profile versions when their contents change.

The wheel build, including `uv sync`, runs `hatch_build.py`, which generates the `newton_usd_schemas.validators._requirements` package from these pages with `usd-profiles-nvidia`. The generated package is not committed; edit the pages instead. The hook gives the modules generated from our pages the Newton copyright header, and the `_api` package and `_protocols.py`, which `usd-profiles-nvidia` copies in unchanged, keep their NVIDIA headers. Capability pages must be named `capability-<name>.md`, and list their requirement pages in a `requirements-table` directive.

## Testing

The unittests can be run in several ways:

```bash
# via uv
uv run --group dev poe test

# in an activated venv
poe test

# individual test discovery
poe test -k test_plugin.TestNewtonPlugin.test_newton_plugin_registered
```

### Test Requirements

New and changed schemas must be tested as thoroughly as the existing suites in `tests/`. This is a merge requirement, not a guideline. The schemas are codeless, so the coverage report does not measure them, and a passing coverage check does not show that a schema change is tested.

Before writing tests, read the existing suites for similar schemas and match their structure and depth. For each schema, the tests must verify:

- Registration, including both the plugin type name and the schema type name.
- Application, including any built-in or auto-applied APIs and the properties they bring.
- Applicability, including prim types the schema must not apply to.
- Every property, each in its own test: absent before the schema is applied, unauthored with the expected fallback value after it is applied, and authorable with a new value. Also check allowed tokens, hard and soft limits, and relationship targets where the schema defines them.

Changes to existing schemas update the matching tests so they still cover every property. Removed or renamed properties need tests that confirm the old name is gone.

Reviewers must confirm that the tests in a PR meet this bar by comparing them against the existing suites. A passing CI run is not enough.
