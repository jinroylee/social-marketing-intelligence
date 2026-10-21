# Campaign recommendation application

Own the save-first composition of campaign recommendation and automatic discovery admission. `CampaignRecommendations.recommend` delegates deterministic/model recommendation to `CampaignStore`, then submits that saved shortlist's coverage need through `AcquisitionTasks`. `read` joins their public views. Construct both owners for the same database/workspace and configure the automation's campaign role at the trusted application boundary.

Campaigns own the immutable coverage policy/clock/inputs and recommendation. Tasks own the one-per-shortlist disposition and task transaction. Preserve this dependency direction: campaign core does not import tasks, and this composition writes no SQL. A failed admission cannot roll back a saved recommendation. Retries reopen both owners' exact historical results; the worker owns later cost waiting/resume. Source/model I/O never belongs in a transaction here.

Read [the automatic discovery contract](../../../docs/campaigns.md#automatic-coverage-and-discovery) before changing scope derivation, admission retries or visibility. Forms/model/source text cannot assign campaign authority, query configuration or spending controls. Discovery completion does not change shortlist history.
