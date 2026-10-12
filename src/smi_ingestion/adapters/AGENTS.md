# Source adapters

This directory contains source-specific collectors and mappers registered through `AdapterRegistry`. A collector bounds I/O and returns `ObservationDraft` values; a mapper interprets that adapter's declared format into `NormalizedBatch`. The runner and shared writer own persistence and canonical identity rules.

Keep source credentials, transport errors, pagination, and source policy inside the collector. Keep mapping deterministic and free of network calls. Adapters must not write database tables or infer campaign facts from a platform handle, language, or engagement count. Treat identifiers from supplied references as hints until source evidence corroborates them.

For TikTok oEmbed, use only documented URL-to-embed reads. Its mapper validates the response transiently and writes no creator facts; it does not parse rendered embeds or profile HTML.

For Bright Data, keep the API credential inside the transport, count each provider request, and treat documented response fields as provisional until a live Japan sample confirms them. For direct web collection, distinguish a bot challenge from an empty, private, or removed profile. Retain each route's own policy and provenance; only corroborated platform IDs and fields may become canonical candidates. The local prototype's technical success is separate from later publication-use review.
