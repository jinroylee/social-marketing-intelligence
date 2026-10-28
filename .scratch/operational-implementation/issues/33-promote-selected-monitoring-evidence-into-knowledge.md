# 33: Promote selected monitoring evidence into knowledge

**What to build:** An operator can deliberately promote selected permitted recent X observations through normal ingestion and publication, with traceable origins.

**Blocked by:** 02: Publish and inspect permitted ingested support; 29: Collect bounded recent X evidence offline.

**Status:** claimed

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** One local selected-observation promotion path; do not fetch new data or publish the whole feed automatically.

- [ ] A trusted explicit selection creates normal source observations/canonical mappings where supported and usable knowledge publications with links back to the monitoring inputs.
- [ ] Promotion preserves source policy, capture times, native identities/namespaces, metric semantics, mapper versions, and unknown identity fields.
- [ ] Retrying the same promotion does not duplicate canonical effects or logical publications.
- [ ] No additional provider request or campaign is created; unselected observations remain solely in the bounded monitoring evidence path.
- [ ] Monitoring and KB/alert copies honor their applicable retention, expiry, and withdrawal dependencies without using promotion to bypass denied support.
- [ ] A local selection/result surface and public integration tests verify lineage, repeat promotion, partial invalid records, and policy changes.

**Spec coverage:** user stories 45, 53, 55, 56, 68; acceptance scenarios T08, T20, T27 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
