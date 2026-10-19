# 14: Compare eligible accounts from current knowledge

**What to build:** A marketer can compare current-KB accounts against a campaign's recorded criteria with exact supporting evidence and explicit unknowns.

**Blocked by:** 03: Search current knowledge and pin result support; 12: Save visible executable campaign criteria.

**Status:** draft — awaiting breakdown approval; not published

**Size:** M — one bounded user-visible journey or extension in a fresh implementation context.

**Scope guard:** Reuse the existing deterministic caption criteria for a bounded KB candidate set; no automatic shortlist saves or LLM assessment yet.

- [ ] Candidates come only from current permitted KB support within the campaign scope and carry the exact retrieved support manifest/profile/brief versions.
- [ ] Stable account identity plus one permitted ingested supporting observation is sufficient for eligibility; incomplete profiles remain explicit.
- [ ] Handle-only or un-ingested references may appear as discovery seeds/gaps but never as supported comparison candidates.
- [ ] Required exclusions and unknown policies affect the displayed assessment; caption language/PR markers do not imply audience geography or contracts.
- [ ] Comparison details expose support, source dates, freshness, gaps, empty results, and actual method without pretending to be an LLM rank.
- [ ] Preparation and reopen tests cover withdrawal races, newer publications, source namespaces, and immutable historical comparisons.

**Spec coverage:** user stories 5, 6, 7, 9, 10, 14, 17, 68; acceptance scenarios T08, T09, T10, T11 (the part exercised by this slice).

**Verification:** Use the owning public operations and the existing integration/HTTP test conventions where applicable. Keep real PostgreSQL/policy behavior; simulate external I/O by default. Update the corresponding product contracts, physical ERD, and local module instructions when their behavior or ownership changes. Run the shared locked checks. A passing test suite does not establish human language or marketer-usefulness validation.
