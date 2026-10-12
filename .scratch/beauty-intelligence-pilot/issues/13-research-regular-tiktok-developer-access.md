# Verify regular TikTok developer access for known creator evidence

Label: wayfinder:research
Type: research
Mode: AFK
Status: resolved
Assignee: Codex research agent
Parent: [Plan a build-ready beauty intelligence pilot](../map.md)
Blocked by: none

## Question

For a solo developer building a commercial marketer decision tool for Japan, which current TikTok developer products can programmatically retrieve and refresh public profile/video evidence for (a) a creator who authorizes the app and (b) an arbitrary known creator who does not? Verify app eligibility, approval and OAuth requirements, supported identifiers and operations, fields, quotas, retention/display/commercial-use rules, and whether the supplied video URL can be used as a seed. Distinguish official documentation from actual project access and an observed sample. Use primary TikTok sources, do not create accounts or acquire data, and write findings to `../research/13-regular-tiktok-developer-access.md`.

## Answer

Current first-party findings are in [Regular TikTok developer access for the first creator sample](../research/13-regular-tiktok-developer-access.md). An individual can register a regular developer app, and sandbox can test a consenting account, but production Display API requires app/product/scope approval and creator OAuth. Its user/video reads include post engagement counts; `user.info.stats` is a separate profile-count scope. It cannot fetch the supplied video or an arbitrary creator without that creator's authorization, and it does not provide discovery. Research Tools have arbitrary-user queries but exclude commercial users; Commercial Content API lacks Japan content coverage; Data Portability covers EEA/UK users only. TikTok's Developer Terms create a material unresolved commercial-use and individual-profiling question for a marketer-facing scoring/database product. No grant, live sample or rights clearance was obtained. This research ticket is resolved at the documentation level only; [source selection](11-select-live-source-and-evidence-scope.md) remains open.
