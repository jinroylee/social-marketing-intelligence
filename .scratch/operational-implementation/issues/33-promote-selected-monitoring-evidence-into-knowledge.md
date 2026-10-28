# 33: Promote selected monitoring evidence into knowledge

**What to build:** An operator can deliberately promote selected permitted recent X observations through normal ingestion and publication, with traceable origins.

**Blocked by:** 02: Publish and inspect permitted ingested support; 29: Collect bounded recent X evidence offline.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One local selected-observation promotion path; do not fetch new data or publish the whole feed automatically.

- [x] A trusted explicit selection creates normal source observations/canonical mappings where supported and usable knowledge publications with links back to the monitoring inputs.
- [x] Promotion preserves source policy, capture times, native identities/namespaces, metric semantics, mapper versions, and unknown identity fields.
- [x] Retrying the same promotion does not duplicate canonical effects or logical publications.
- [x] No additional provider request or campaign is created; unselected observations remain solely in the bounded monitoring evidence path.
- [x] Monitoring and KB/alert copies honor their applicable retention, expiry, and withdrawal dependencies without using promotion to bypass denied support.
- [x] A local selection/result surface and public integration tests verify lineage, repeat promotion, partial invalid records, and policy changes.

**Spec coverage:** user stories 45, 53, 55, 56, 68; acceptance scenarios T08, T20, T27 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.


## Implementer handoff

- Runtime implementation: `67c58b6dab6bfa0db7a0a02693d7be9c6d96ad02`; latest integration metadata merged before clean frozen checked head `48cc8052cb604c6c5872ccdc1a7215a8e8c1556e`.
- Required offline locked shared gate **passed exit 0**, **794 tests in 731.13s**, completed session **78065**. Durable worker `verification/ticket-33/shared.{json,log}` records exact command/head/start/finish/session/exit. No completed unchanged gate was repeated.
- Offline wheel independently verified: **397759 bytes**, **192 unique entries**, SHA-256 `890aeafc00bd710601770833479d2b32742a42dfbf911c01023fb741da02441a`; **88 source/archive pairs**, including sixteen SQL schemas, both review assets and all 29 packaged guidance pairs. [Report](../reports/ticket-33.md), [exact manifest](../reports/ticket-33-wheel-manifest.json) and [verifier](../reports/verify-ticket-33-wheel.py) retain reviewable evidence.
- All acceptance criteria have local public-operation/HTTP evidence. The issue stays **claimed** pending independent merger gating, artifact verification and resolution. No runtime/test/product-doc/guidance change followed frozen PASS; only this handoff, own report and exact manifest/verifier metadata changed. Artifacts remain in the persistent worker worktree for verified root archival/relocation before eventual cleanup. No live source/model/paid call, external message, push, PR, deployment or cleanup occurred; no human-language, marketer-usefulness or live-readiness claim is made.
