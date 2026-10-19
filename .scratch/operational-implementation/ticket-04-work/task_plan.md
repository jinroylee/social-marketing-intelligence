# Ticket 04 plan

1. Read contracts and claim ticket — complete.
2. Public task-to-knowledge red/green slices — complete.
3. HTTP/CLI and boundary regressions — complete.
4. Product/ERD/instruction updates — complete.
5. Full shared checks and packaging — complete.
6. Final report — complete; implementation ready for local commit.

## Next Step
Hand the local implementation commit to the merger; ticket 04 remains claimed until integrated checks pass.

## Errors Encountered
Expected TDD reds: missing smi_tasks; empty manifest reported failure; unchanged capture reported usable_update; absent HTTP route configuration argument; absent CLI subcommand. Fixed with the minimum owning implementations. Initial tracer test used the wrong existing query manifest key (publication.producer); corrected to the documented publication_producer field.
