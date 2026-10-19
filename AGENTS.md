# Engineering guidance

These rules apply throughout the repository. Follow any more specific `AGENTS.md` in the directory you are changing.

## Architecture

- Read the relevant code, callers, tests, and local conventions before editing. Keep each change focused on the requested behavior.
- Give modules cohesive responsibilities and small, explicit interfaces. Keep dependency direction clear and acyclic; put shared behavior with its natural owner rather than in a catch-all utility.
- Separate core decisions from I/O and framework concerns when that boundary improves clarity. Make contracts, invariants, side effects, and failure behavior explicit. Introduce abstractions for concrete needs, not anticipated ones.
- Prefer composition and straightforward data flow. Avoid hidden mutable state, circular dependencies, and reaching through a module's interface into its internals.

## Code and verification

- Run `uv run --locked python tools/check.py` for the shared local/CI checks. See `docs/development.md` for prerequisites and static-only checks.

- Use precise names, simple control flow, suitable types, and the repository's established formatting. Handle errors at the right boundary with useful context.
- Write concise docstrings for public interfaces and non-obvious behavior, covering inputs, results, invariants, errors, or side effects where relevant. Use comments to explain intent, constraints, and tradeoffs; keep them accurate as code changes.
- When behavior changes, add or update tests for important paths and edge cases. Run the relevant checks and resolve failures before finishing.

## Local instructions

- Keep `docs/` aligned with the intended product and the current implementation. When changing architecture, persistence, module interfaces or operational behavior, update the corresponding architecture description, ERD or durable ADR in the same change. Read `docs/README.md` for the documentation structure.
- Use Markdown and Mermaid where they express the design clearly. Distinguish implemented behavior from accepted future design. Keep prototype chronology, session logs and implementation tracking in `.scratch/`; product ADRs explain durable trade-offs rather than recounting experiments.

- When implementing a module or submodule with a substantial, distinct role, add an `AGENTS.md` in its directory. Explain its responsibility, interface, dependencies, invariants, local rules, and likely antipatterns without repeating this file.
- Every `AGENTS.md` must have a sibling `CLAUDE.md` that is a relative symlink to `AGENTS.md`. Keep one source of truth; update or remove the pair together.
