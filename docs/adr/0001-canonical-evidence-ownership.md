# Separate canonical evidence from business knowledge and decisions

Status: accepted

Source observations and canonical account/content identities belong to ingestion; semantic interpretations, generated recommendations and human decisions belong to their own modules and tables in the same PostgreSQL database. Downstream modules use explicit evidence interfaces instead of adapter schemas or a universal ingestion entity table. This preserves source provenance and enables independent monitoring and campaign workflows without making a collector responsible for business judgments.

The trade-off is explicit references and interfaces between owners rather than convenient cross-module writes. Product entities and decision revisions can evolve without changing source identity semantics; new evidence routes need only satisfy the acquisition contract.
