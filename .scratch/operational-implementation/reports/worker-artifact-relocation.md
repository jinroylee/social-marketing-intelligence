# Preserved worker verification artifacts

Completed ticket 26–35 artifacts have verified persistent copies in the integration worktree. Original worktrees and historical paths remain intact. No completed gate was rerun, and no worktree was removed. The local verification directory is intentionally excluded from Git; this document records the usable archive locations and identities.

Each archive contains the complete original ticket verification directory and its own committed report, exact wheel manifest and standalone verifier. Every member was compared with the original file by byte size and SHA-256. The machine-readable `verification/worker-archives/relocation-index.json` records original absolute paths, archive-member paths, worker heads, per-file hashes and current archive locations.

| Ticket | Root-relative archive under `.scratch/operational-implementation/` | Members | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| 26 | `verification/worker-archives/ticket-26-worker-artifacts.tar.gz` | 39 | 289074 | `ae3bb29dee8f907c781959bcc198368553ebdacbf24e09e50df55e33a1c52a89` |
| 27 | `verification/worker-archives/ticket-27-worker-artifacts.tar.gz` | 31 | 291820 | `aeeb358cece525e8e370fa9b6db01699ae57dd084431914125b5131a2060f558` |
| 28 | `verification/worker-archives/ticket-28-worker-artifacts.tar.gz` | 40 | 304932 | `ef781758ac1d4207e9901fa069aad647c99d08b2bf410ed53c52ab649de5ce14` |
| 29 | `verification/worker-archives/ticket-29-worker-artifacts.tar.gz` | 35 | 328046 | `53177649f7806e83a69057a0cae716242c4a4b78db0cf0047d60acf0be4c9c6e` |
| 30 | `verification/worker-archives/ticket-30-worker-artifacts.tar.gz` | 34 | 344174 | `c4af2b881bfedf96a1b0c6a404c3b6fed5d1aeaccf18fcf89a9091a3b00fca72` |
| 31 | `verification/worker-archives/ticket-31-worker-artifacts.tar.gz` | 51 | 718927 | `3ab522ca97efb765ef885fff91e6cdad01dff74c8d1e0018c5a0a5c1a97b006f` |
| 32 | `verification/worker-archives/ticket-32-worker-artifacts.tar.gz` | 46 | 360589 | `735f3e0c6a5a73de806d0bde40ebb92b7ce94197c58244cdd61d2fb9765eea14` |
| 33 | `verification/worker-archives/ticket-33-worker-artifacts.tar.gz` | 38 | 369596 | `9b13f15039e674a87cf29bbc9b6e6898a018c3c49a6d75b969b2c714dd97d0d1` |
| 34 | `verification/worker-archives/ticket-34-worker-artifacts.tar.gz` | 42 | 432887 | `94d98c27a4fb212e2e54a6c949871166ce82fc487f6441a3adea7d40aaccb068` |
| 35 | `verification/worker-archives/ticket-35-worker-artifacts.tar.gz` | 39 | 406294 | `9bde6094793f7a93527d868350d251bd53f19a8c5a5946792ee6b58ebb9084dd` |

Ticket 31’s earlier prepared nested archive is preserved as an unchanged member of its root archive. At final cleanup, verify these identities again before removing clean merged worktrees and update the relocation index. Older missing temporary artifacts remain unavailable as previously documented; no copy has been invented.

Ticket 34 additionally preserves its seven fetched primary documents, exact source-identity index and committed contract research note.
