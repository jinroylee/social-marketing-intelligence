# Preserved worker verification artifacts

Ticket 26–38 verification, ticket 39 preparation and all three final-fixer snapshots have persistent archives and usable extracted copies in this integration worktree. Every retained member was compared by size and SHA-256 with its archive; available original files were verified before their worktrees were removed. All branch refs survive.

The intentionally Git-excluded `verification/worker-archives/relocation-index.json` records original paths, frozen/worker heads, archive/member hashes, current retained paths and actual removal times. Keep the full `verification/` directory when moving this checkout. Its SHA-256 at final cleanup is `6adf7bcb207b0a2411845005ae44fca261db50ffd7bf674bc7cb70e4d1d4c011`.

| Snapshot | Archive under `verification/worker-archives/` | Files | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| 26 | `ticket-26-worker-artifacts.tar.gz` | 39 | 289074 | `ae3bb29dee8f907c781959bcc198368553ebdacbf24e09e50df55e33a1c52a89` |
| 27 | `ticket-27-worker-artifacts.tar.gz` | 31 | 291820 | `aeeb358cece525e8e370fa9b6db01699ae57dd084431914125b5131a2060f558` |
| 28 | `ticket-28-worker-artifacts.tar.gz` | 40 | 304932 | `ef781758ac1d4207e9901fa069aad647c99d08b2bf410ed53c52ab649de5ce14` |
| 29 | `ticket-29-worker-artifacts.tar.gz` | 35 | 328046 | `53177649f7806e83a69057a0cae716242c4a4b78db0cf0047d60acf0be4c9c6e` |
| 30 | `ticket-30-worker-artifacts.tar.gz` | 34 | 344174 | `c4af2b881bfedf96a1b0c6a404c3b6fed5d1aeaccf18fcf89a9091a3b00fca72` |
| 31 | `ticket-31-worker-artifacts.tar.gz` | 51 | 718927 | `3ab522ca97efb765ef885fff91e6cdad01dff74c8d1e0018c5a0a5c1a97b006f` |
| 32 | `ticket-32-worker-artifacts.tar.gz` | 46 | 360589 | `735f3e0c6a5a73de806d0bde40ebb92b7ce94197c58244cdd61d2fb9765eea14` |
| 33 | `ticket-33-worker-artifacts.tar.gz` | 38 | 369596 | `9b13f15039e674a87cf29bbc9b6e6898a018c3c49a6d75b969b2c714dd97d0d1` |
| 34 | `ticket-34-worker-artifacts.tar.gz` | 42 | 432887 | `94d98c27a4fb212e2e54a6c949871166ce82fc487f6441a3adea7d40aaccb068` |
| 35 | `ticket-35-worker-artifacts.tar.gz` | 39 | 406294 | `9bde6094793f7a93527d868350d251bd53f19a8c5a5946792ee6b58ebb9084dd` |
| 36 | `ticket-36-worker-artifacts.tar.gz` | 37 | 407615 | `fdcb6d3c84cf00b4776091e79a0e8296f27ed8f8a5df54ccbb7d129f2b1b3ffa` |
| 37 | `ticket-37-worker-artifacts.tar.gz` | 39 | 418363 | `3a2939b26539d6ba25bf2d3f46fbaab9ed4c6ce9fb7738944447ff64325e0b52` |
| 38 | `ticket-38-worker-artifacts.tar.gz` | 30 | 424864 | `7fd59cd93bce0a0ae3a8302ac40cd2c81ddca738cb1e8299fabb3122f1c2ded4` |
| 39 | `ticket-39-worker-artifacts.tar.gz` | 3 | 9129 | `013cb558e65e8f52f6e3097334eaa58017a8e7db0f4a02940946b858957198f2` |
| final_review_fixes | `final-review-fixes-worker-artifacts.tar.gz` | 25 | 442108 | `9adfc9cb82fb3b76eb07c8ef0979946153f70204751fc9fccc6a09d1576c5b33` |
| final_temporal_fix | `final-temporal-fix-worker-artifacts.tar.gz` | 28 | 442772 | `b41d55344a70ce885b7e3bf819aa9748b67e7782bb4821e8b9c8b0821b45d568` |
| final_cost_fixtures | `final-cost-fixtures-worker-artifacts.tar.gz` | 26 | 440918 | `c3ae3aca48b405ed4393d59257ae8ed9c87c2889e81cd5da0e90ed68fb00496a` |

Usable copies preserve each original relative `.scratch/operational-implementation/` tree under `verification/retained-workers/ticket-N/`, `final-review-fixes/`, `final-temporal-fix/` and `final-cost-fixtures/`. Committed reports/manifests/verifiers also remain in this tree. Historical verifiers require their recorded frozen source commit; the latest cost-fixture verifier matches the current tree.

All 17 archives and 583 retained files were checked before removing the last worker. All 15 available clean merged worktrees were removed without force; 15 known already-missing ticket 11–25 registrations were pruned separately. Branch refs were preserved. Only the integration worktree remains. The latest retained standalone verifier successfully replayed after removal; exact arguments, output and exit 0 are in `verification/post-cleanup-wheel-verification.*`.

Ticket 31’s earlier nested archive remains unchanged inside its root archive. Ticket 34 retains seven fetched primary documents, their source-identity index and its committed contract research note. Ticket 39’s three files contain preparation only; actual human validation is pending.

Untracked verification artifacts for older temporary ticket 11–25 worktrees had disappeared before this cleanup. Their committed reports/manifests and branch history survive; missing raw logs/wheels remain unavailable. No replacements were invented.
