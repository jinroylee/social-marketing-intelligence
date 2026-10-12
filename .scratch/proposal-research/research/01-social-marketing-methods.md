# Evidence-backed methods for Social Marketing Intelligence

Research date: 2026-09-22  
Question: Which established and emerging methods should shape a Social Marketing Intelligence Platform for brand and agency teams, with particular attention to beauty in South Korea and Japan?

## Executive findings

1. **Build the product around decisions and estimands, not a universal score.** “Creator fit,” “brand health,” “trend strength,” “attention,” and “ROI” describe different decisions and evidence. Each result should name its intended decision, subject, target population, time window, observations, metric definition, method version, uncertainty, and known coverage gaps. AMEC’s current principles similarly require measurable objectives, relevant channels, qualitative and quantitative analysis, and separate reporting of outputs, outcomes, and impact. ([AMEC Barcelona Principles 4.0, 2025](https://amecorg.com/wp-content/uploads/2025/06/Barcelona-Principles-V4.0-Ebook-FINAL-Compressed.pdf); [AMEC Integrated Evaluation Framework](https://amecorg.com/amecframework/home/framework/introduction/))
2. **Treat social listening as observed conversation, not public opinion.** Platform users, public posters, query matches, and accessible content are selected populations. User- and post-level sampling can overrepresent frequent posters, and even demographic reweighting can fail when attributes are inferred or cells are sparse. The product should expose source coverage, collection rules, missingness, deduplication, and uncertainty; it should not project mention shares or sentiment to a national population without an appropriate probability sample or validated correction. ([MRC Social Media Measurement Guidelines](https://mediaratingcouncil.org/sites/default/files/News/General-Announcements/MRC%20Social%20Measurement%20Guidelines%20v1.0%20Final.pdf); [Bandyopadhyay et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9714525/); [Wang et al., 2023](https://pubmed.ncbi.nlm.nih.gov/36721461/))
3. **Use local-language, aspect-level, and multimodal evaluation.** Korean and Japanese tokenization, slang, code-switching, honorifics, negation, and platform style can change model behavior. Beauty discussion is often aspect-specific: a post can praise color and criticize texture, staying power, shipping, or price. OCR, speech-to-text, captions, frames, and comments should remain separately attributable observations before fusion. Korean and Japanese general-language benchmarks show that locally developed evaluation matters, but they do not validate a model for beauty social listening; a labeled in-domain test set is still required. ([KLUE](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/98dce83da57b0395e163467c9dae521b-Paper-round2.pdf); [JGLUE](https://aclanthology.org/2022.lrec-1.317.pdf); [Nguyen et al., 2025](https://aclanthology.org/2025.paclic-1.76.pdf))
4. **Rank creators with decomposed, outcome-specific evidence.** Credibility, audience relationship, informational or entertainment value, brand/product fit, sponsor salience, content originality, follower scale, historical performance, audience overlap, availability, cost, and risk can matter differently by campaign objective. Research consistently rejects a simple “more followers is better” rule, while the size and direction of specific effects vary by context. Show the evidence components and sensitivity to weights rather than hiding them in one fit score. ([Pan et al., 2025 meta-analysis](https://doi.org/10.1007/s11747-024-01052-7); [Goldilocks Influencers](https://journals.sagepub.com/doi/full/10.1177/00222429221125131); [Influencer Effectiveness](https://journals.sagepub.com/doi/pdf/10.1177/00222429221102889); [Influencer–product fit experiment](https://doi.org/10.1080/02650487.2021.1994205))
5. **Make authenticity a reviewable risk assessment.** Suspicious follower growth, synchronized following, follow-back networks, audience geography mismatch, implausible engagement, repeated comments, and deleted/reposted content are useful signals. They are not proof of purchased followers or intent. Preserve raw evidence, distinguish account-, audience-, and content-level signals, validate at an operating threshold, and route consequential cases to human review. Peer-reviewed detection results are promising but data- and platform-specific. ([Pacheco et al., 2024](https://doi.org/10.1140/epjds/s13688-024-00499-6); [Khosla et al., 2024](https://ojs.aaai.org/index.php/ICWSM/article/view/31321); [MRC Invalid Traffic Addendum](https://www.mediaratingcouncil.org/sites/default/files/Standards/IVT%20Addendum%20Update%20062520.pdf))
6. **Begin portfolio planning with transparent scenarios.** A shortlist should expose budget, creator capacity, audience overlap, platform/market mix, timing, category conflicts, minimum commitments, and concentration risk. Mathematical portfolio optimization and influence-maximization research can formalize these constraints, but outputs depend on uncertain response, cost, overlap, and diffusion assumptions. Until those inputs are calibrated, compare feasible scenarios and ranges rather than presenting an “optimal” roster. ([Perrault et al., 2020](https://proceedings.mlr.press/v119/perrault20a/perrault20a.pdf); [Jiang et al., 2024](https://doi.org/10.1016/j.jik.2024.100502))
7. **Separate attribution from incrementality.** Codes, affiliate links, UTMs, pixels, and platform-attributed conversions describe observed paths under a rule. They do not reveal what would have happened without the campaign. Randomized user- or geo-level lift is the strongest practical causal design when feasible; matched markets, synthetic controls, interrupted time series, and calibrated marketing-mix models can help when randomization is unavailable, but require explicit assumptions and sensitivity analysis. ([MRC Outcomes and Data Quality Standards](https://www.mediaratingcouncil.org/sites/default/files/Standards/MRC%20Outcomes%20and%20Data%20Quality%20Standards%20%28Final%29.pdf); [Google Conversion Lift](https://support.google.com/google-ads/answer/12003020?hl=en); [Gordon et al., 2019](https://gwern.net/doc/statistics/causality/2019-gordon.pdf))
8. **Treat attention and content features as intermediate evidence.** Retention curves, watch time, scroll-stop signals, visual/audio features, topics, hooks, and creator delivery can diagnose how content was consumed. They are not business outcomes. The 2025 IAB/MRC guidelines establish a common framework for attention measurement but explicitly require validation, disclosure, privacy safeguards, and care when connecting attention to outcomes. Creative performance claims should ultimately be tested through experiments. ([IAB/MRC Attention Measurement Guidelines, 2025](https://www.mediaratingcouncil.org/sites/default/files/Standards/IAB_MRC_Attention_Measurement_Guidelines_November_2025.pdf); [YouTube Analytics metrics](https://developers.google.com/youtube/analytics/metrics))
9. **Version brand-safety, disclosure, and beauty-claim rules by jurisdiction and effective date.** South Korea and Japan both regulate undisclosed commercial relationships and misleading cosmetics claims, but the responsible party, required presentation, product categories, and permitted efficacy language differ. A shared core can represent a disclosure, claim, evidence, risk, and review; market extensions should supply language- and category-specific policies. The system should assist review and preserve evidence, not declare legal compliance. ([Korea Fair Trade Commission enforcement](https://www.ftc.go.kr/eng/contents.do?key=557); [Japan Consumer Affairs Agency stealth-marketing FAQ](https://www.caa.go.jp/policies/policy/representation/fair_labeling/faq/stealth_marketing/); [Korea MFDS cosmetics advertising](https://www.mfds.go.kr/wpge/m_646/de050601l0025.do); [Japan MHLW advertising regulation](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/koukokukisei/index.html))
10. **Prioritize a narrow, auditable first product.** For a small team, the strongest first slice is evidence-backed brand listening plus creator shortlisting, a campaign measurement plan, and a learning record. It should include manual review for entity, language, safety, and authenticity ambiguity. General portfolio optimization, autonomous recommendations, generalized causal claims, and cross-market benchmark promises should wait until the platform has outcome data and evaluation sets.

## Evidence and maturity labels

- **Established:** a recognized measurement or regulatory standard, a well-understood statistical method, or a conclusion supported across substantial peer-reviewed evidence. “Established” does not mean universally valid without assumptions.
- **Operationally mature:** used in production with accepted procedures, while results remain dependent on coverage, implementation, platform, market, or campaign context.
- **Emerging:** credible peer-reviewed or technical evidence exists, but generalization, calibration, or operational practice is still limited.
- **Vendor capability/claim:** an official platform product, method description, or reported result. It is useful evidence about availability and implementation, not independent proof of comparative effectiveness.

Confidence is method-specific. A probability from a classifier, a sampling confidence interval, a Bayesian credible interval, inter-rater agreement, and an evidence-strength grade are not interchangeable and should never share an unlabeled generic `confidence` field.

## Methodology matrix

| Methodology | Decision supported | Required observations | Method and output | Useful metrics | Uncertainty treatment | Principal limitations | Maturity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Query-based social listening and entity resolution | What conversation concerns the brand, product, competitor, creator, or issue? | Source-native IDs; text, captions, OCR/ASR; links and timestamps; language; query and access scope; identity evidence | Versioned Boolean/semantic retrieval, deduplication, language ID, named-entity linking, triage; output is an evidence-backed set of mentions and linked entities | Retrieval precision/recall/F1 on a labeled set; unresolved rate; duplicate rate; source/time coverage; ingestion lag | Per-class error, review-needed state, source coverage and missing intervals | APIs and public content are incomplete; names are ambiguous; deleted/private content is absent; frequent posters are overrepresented | Operationally mature, with local validation required |
| Aspect, topic, stance, and sentiment analysis | What is being discussed, by whom, and with what evaluation? | Retrieved content plus context, language, author/account, media-derived text, aspect taxonomy, human labels | Multi-label classification or extraction; aspect-based sentiment; topic clustering followed by naming/review; output is claim-level labels with evidence spans | Macro/per-class F1; confusion matrix; calibration; abstention/review rate; stability across time/platform/market | Label distributions, calibrated probabilities, disagreement and abstention; stratified error analysis | Sarcasm, mixed sentiment, code-switching and aspect scope; topic clusters are model- and corpus-dependent; demographic inference is especially sensitive | Mature for narrow taxonomies; emerging for robust cross-language multimodal use |
| Trend, burst, and event detection | Is conversation changing enough to investigate or act? | Time-binned counts/rates, baseline history, source volume, creator/content graph, external-event annotations | Seasonal baselines, burst or change-point detection, robust anomaly scoring, evidence clustering; output is an alert with contributing content and alternative explanations | Alert precision; false alerts per period; detection delay; lead time; persistence; stability under backfill | Posterior/change probability or empirical threshold bands; sensitivity to binning and seasonality | Platform/news events, collection outages, spam, and denominator changes can mimic trends; virality prediction remains weak | Statistical detection established; social interpretation context-dependent |
| Creator discovery and fit ranking | Which creators merit research or outreach for this brief? | Creator/account identity; content and collaboration history; audience estimates; brand/product/topic evidence; costs/availability where authorized; outcome/risk history | Eligibility filters plus multi-criteria ranking, retrieval, and human review; output is a decomposed shortlist with evidence | Precision@k or reviewer acceptance; criterion coverage; historic outcome by objective; ranking stability; diversity/concentration | Score component ranges, missing-evidence flags, sensitivity to weights, out-of-sample evaluation | Audience data may be modeled or unavailable; past sponsored performance is confounded; fit varies by objective, creative, market and product | Operationally mature as decision support; causal ranking evidence limited |
| Audience authenticity and manipulation risk | Which accounts or metrics require verification or exclusion? | Time-series follower/engagement data; audience geography; reciprocity and synchronization; comment patterns; platform invalid-traffic signals | Rule/model ensemble and case review; output is a risk assessment with signal-level evidence, not an accusation | Precision/recall at chosen threshold; false-positive rate; reviewer agreement; coverage; stability | Threshold-specific validation, indeterminate state, reason codes, source freshness | Ground truth is scarce; coordinated activity may be legitimate; platform visibility changes; intent cannot be inferred from anomalies alone | Emerging to operationally mature, depending on signal access |
| Creator portfolio scenario planning | Which feasible mix best balances expected outcome, reach, learning, cost, and risk? | Shortlisted creators; cost and constraints; overlap estimates; capacity/timing; expected outcome distributions; scenario objectives | Constrained scenario enumeration or optimization; output is several feasible portfolios with trade-offs and sensitivity | Expected incremental outcome range; marginal reach; overlap; spend; concentration; constraint violations; downside risk | Parameter distributions, robust scenarios, sensitivity/frontier rather than point optimum | Response and overlap estimates are uncertain; network diffusion assumptions rarely transport; “optimal” is model-relative | Emerging for optimization; scenario comparison is operationally mature |
| Campaign planning and measurement design | What should run, for whom, and how will success be judged? | Business objective; audience; interventions; budget; channel roles; outcome hierarchy; baseline and detectable effect; tracking and experiment feasibility | Logic model plus preregistered measurement plan; output is brief, KPI dictionary, instrumentation plan, test design and decision rules | Delivery, exposure, intermediate outcomes, business outcomes; MDE/power; planned sample; data quality | Predeclared estimand, target population, horizon, power, exclusions, quality thresholds | Retrofitted objectives invite metric shopping; platform metrics differ; small effects require large samples | Established |
| Multimodal content and creative intelligence | Which creative patterns help explain attention, comprehension, response, or risk? | Video frames, audio, captions, OCR, ASR, comments, edits, metadata, authorized retention/outcome data | Shot/scene and speech/text features, embeddings and clustering, human coding, controlled creative experiments; output is searchable evidence and hypotheses | Extraction coverage/error; retention curves; watch ratio; recall of known attributes; experimental lift by outcome | Propagate extraction error; cluster stability; holdout performance; experimental intervals | Embeddings are not explanations; retention is selected/descriptive; observational feature associations are confounded | Retrieval mature; generalized performance prediction emerging |
| Brand safety, suitability, disclosure, and claims review | Is content eligible and appropriate for this brand, product, audience, and market? | Content evidence; placement/context; brand policy; campaign relationship and compensation; product category; jurisdiction/effective date; claim substantiation | Versioned policy rules, taxonomy classification, human review and escalation; output is reason-coded risk, eligibility and evidence package | Policy coverage; false-negative/positive rate; reviewer agreement; incident rate; review latency | Severity and review state; policy/version provenance; abstention for ambiguity | Safety differs from brand-specific suitability; context and language are hard; regulations change; automated review cannot certify compliance | Operationally mature with human/legal governance |
| Descriptive attribution and performance reporting | Which tracked paths and platform-accounted outcomes are associated with activity? | Spend/delivery; exposure/click/view events; UTMs/codes/affiliate records; pixel/server events; conversion definitions; identity/consent state | Deterministic or model-based attribution under declared rules; output is a reconciled performance report | Reach/frequency, views, engagement, conversions, revenue, CPA/ROAS under each rule; unattributed share | Data-quality flags, attribution-window sensitivity, identity-match coverage, reconciliation differences | Attribution rules allocate credit but do not estimate the counterfactual; privacy loss, walled gardens and self-reporting create gaps | Established for accounting; invalid as causal proof by itself |
| Randomized lift and geo experiments | What incremental outcome did the campaign cause? | Random assignment or randomized geographies; exposure eligibility; outcomes; pre-period covariates; contamination and compliance data | Intention-to-treat and, where justified, treatment-on-treated analysis; user-level lift, geo experiment, or platform lift study | Absolute/relative incremental outcome, incremental cost, iROAS/iCPA, confidence interval, power, balance | Confidence/credible intervals, randomization inference, attrition/contamination checks, sensitivity | Platform study access and black boxes; spillovers/noncompliance; low base rates and small effects; external validity | Established when implemented correctly; vendor studies need transparent assumptions |
| Quasi-experiments and calibrated MMM | What is the likely contribution of channels over time when randomization is incomplete? | Time-series spend/exposure/outcomes; seasonality, price/promotions and confounders; geo or untreated controls; experiment priors | Matched markets, synthetic controls/Bayesian structural time series, or Bayesian MMM with carryover/saturation; output is an assumption-bound counterfactual or response distribution | Incremental effect/contribution, posterior ROI/response, predictive error, placebo/pretrend checks, calibration fit | Posterior intervals, alternative specifications/priors, placebo and holdout tests, sensitivity to unobserved confounding | No method repairs absent confounders automatically; MMM can be weakly identified; granular creator effects often lack data | Established methods, highly context-dependent operational validity |
| Organizational learning | What should be reused, challenged, or tested next? | Frozen briefs, decisions, evidence snapshots, method/policy versions, outcomes, reviews, experiment records and corrections | Decision log, evidence graph, post-test synthesis, reusable playbook and test backlog; output is a traceable learning record | Evidence reuse; decision cycle time; share of claims with provenance; replication/transport success; unresolved conflicts; calibration over time | Preserve contradictory results and scope conditions; grade evidence strength and transportability | Publication and winner bias, metric drift, missing failures, and retrospective storytelling | Established management practice; product implementation is organization-specific |

## Cross-cutting measurement architecture

### Start with an outcome hierarchy

For each campaign, connect the business decision to a small hierarchy:

1. **Inputs and activities:** budget, creator contracts, assets, placements, timing.
2. **Outputs:** eligible delivery, content published, viewable/qualified exposure, observed reach and frequency.
3. **Intermediate outcomes:** recall, comprehension, consideration, search, site behavior, sampling, retailer actions.
4. **Business outcomes:** incremental qualified leads, conversions, sales, retention or brand value under a defined horizon.
5. **Learning outcome:** which uncertainty the campaign reduced and what decision changes next.

AMEC’s framework and taxonomy formalize the distinction among inputs, activities, outputs, outtakes, outcomes and impact; MRC’s outcome standards distinguish attribution from incrementality. The product should preserve those categories rather than allow every metric to become a KPI. ([AMEC taxonomy](https://amecorg.com/amecframework/home/supporting-material/taxonomy/); [MRC Outcomes and Data Quality Standards](https://www.mediaratingcouncil.org/sites/default/files/Standards/MRC%20Outcomes%20and%20Data%20Quality%20Standards%20%28Final%29.pdf))

### Make every analytical result self-describing

A result should carry at least:

- decision and estimand: what question the number answers;
- subject, target population, market, platform and observation window;
- source, access method, query/inclusion rule and collection coverage;
- metric definition, unit, denominator, attribution window and version;
- rule/model/prompt and version, training/evaluation population where relevant;
- uncertainty semantics and interval or threshold;
- missingness, known exclusions and last observation time;
- evidence artifacts and reviewer/approval state;
- supersession history when definitions, data or judgments change.

The 2026 AMEC Data Quality Principles make measurement quality an explicit governed process and call for method-appropriate evaluation, including precision, recall and F1 where classifiers are used. These are industry principles rather than universal numeric acceptance thresholds; thresholds should be selected from the decision cost and monitored by slice. ([AMEC Data Quality Principles, 2026](https://amecorg.com/wp-content/uploads/2026/05/AMEC-Data-Quality-Principles.pdf))

## Social listening and brand intelligence

### Collection and retrieval

Define the accessible universe before interpreting it: platforms, surfaces, public/authorized content, countries/languages, query rules, time windows, deletion handling, rate limits and outages. Retain the exact query and source-native IDs so a result can be audited and, where terms allow, replayed. Separate direct observations from vendor estimates and inferred attributes.

Use a retrieval cascade:

1. high-precision identifiers and aliases for known brands, products and creators;
2. context rules for ambiguous terms, spelling variation, transliteration and hashtags;
3. semantic retrieval for recall, followed by a narrow classifier or review;
4. entity resolution with `match`, `non-match`, and `needs review` outcomes;
5. deduplication that preserves repost/quote/reuse relationships rather than erasing diffusion.

Evaluate retrieval against stratified labeled samples from each platform, language, market, product type and traffic regime. Precision alone can hide missed conversation; recall alone can flood analysts with irrelevant material. Report both, plus source coverage. MRC’s guidelines require disclosure of assumptions, collection limitations and comparable metric definitions, and caution that social-listening results are generally not projectable to all users. ([MRC Social Media Measurement Guidelines](https://mediaratingcouncil.org/sites/default/files/News/General-Announcements/MRC%20Social%20Measurement%20Guidelines%20v1.0%20Final.pdf))

### Interpretation

Use hierarchical, versioned taxonomies: category → product/brand → aspect → claim/topic → stance/sentiment. Allow multi-label outputs and retain the evidence span or timecode. A beauty post may mention a product favorably while criticizing one attribute; a single document-level polarity discards that structure. A 2025 beauty-domain study demonstrates a practical pipeline combining video/text observations, speech recognition, normalization, brand identification and aspect-polarity classification, including aspects such as color, texture, smell, staying power, price, shipping and packaging. Its results are useful as a blueprint, not evidence that the reported accuracy transfers to Korea, Japan or a different platform. ([Nguyen et al., 2025](https://aclanthology.org/2025.paclic-1.76.pdf))

Do not infer demographics, skin conditions, ethnicity or other sensitive traits merely because a model can. Use authorized audience aggregates where appropriate, record whether an attribute is declared, observed, inferred or modeled, and test for differential error. For population claims, obtain survey or panel evidence designed for the target population. Research on Twitter/X sampling shows that post-level samples can overrepresent frequent posters, while poststratification can improve or worsen prediction depending on demographic inference and cell support. ([Bandyopadhyay et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9714525/); [Wang et al., 2023](https://pubmed.ncbi.nlm.nih.gov/36721461/))

### Trends and events

Create alerts from deviations against platform- and query-specific baselines, not raw volume thresholds. Established statistical tools include burst detection and online change-point detection; both still require choices about time bins, seasonality, hazard/baseline assumptions and alert thresholds. ([Kleinberg, 2002](https://www.cs.cornell.edu/home/kleinber/bhs.pdf); [Adams and MacKay, 2007](https://arxiv.org/abs/0710.3742))

An alert should include the changed measure, baseline, probability/score, earliest detection, contributing content/accounts, source-volume changes, potential spam or collection issues, and an analyst disposition. “Trend” should mean a detected change in a defined observed corpus; “will become popular” is a separate forecast requiring prospective evaluation.

## Creator intelligence

### Discovery, fit and effectiveness

First apply hard eligibility constraints: market and language, platform, content category, conflicts/exclusivity, safety rules, audience access, budget range, availability and required deliverables. Rank only the eligible set.

Then expose decision-specific evidence, for example:

- **relevance:** recent content and collaboration evidence tied to brand, product, beauty aspect or audience need;
- **communication value:** originality, expertise, clarity, entertainment/informational value and format competence;
- **relationship:** observed audience interaction quality, community continuity and credible identification signals;
- **commercial evidence:** prior sponsored outcomes under comparable objectives, with spend, exposure and attribution limitations;
- **audience:** authorized/estimated composition, geography, duplication and uncertainty;
- **risk and operations:** disclosure history, claims/safety flags, authenticity signals, content reliability, cost and capacity.

A 2025 meta-analysis covering 1,531 effect sizes from 251 papers found that different influencer and post attributes mattered for different response types, with meaningful moderators and heterogeneity. Other multi-method and experimental work reports nonlinear or interacting effects involving follower count, fit, posting activity, positivity, originality and sponsor salience. These results support a conditional, decomposed model; they do not supply portable global weights. ([Pan et al., 2025](https://doi.org/10.1007/s11747-024-01052-7); [Goldilocks Influencers](https://journals.sagepub.com/doi/full/10.1177/00222429221125131); [Influencer Effectiveness](https://journals.sagepub.com/doi/pdf/10.1177/00222429221102889); [Influencer–product fit experiment](https://doi.org/10.1080/02650487.2021.1994205))

Official creator marketplaces can supply authorized discovery, audience and performance information. Instagram describes machine-learning recommendations, creator/audience filters and creator portfolios; TikTok One describes creator discovery and reporting. These are useful product capabilities but their ranking validity, coverage and comparative lift are vendor claims unless independently evaluated. ([Instagram Creator Marketplace](https://about.fb.com/news/2024/02/creator-marketplace-for-brands-and-creators-to-collaborate-on-instagram/); [TikTok One](https://ads.tiktok.com/business/en-US/blog/tiktok-one-creative-platform))

### Authenticity

Use multiple layers:

- account history: growth discontinuities, age, handle changes and repeated inactivity/revival;
- audience/network: follow-back density, synchronized following, suspicious cohorts and geography/language mismatch;
- content/engagement: duplicated or semantically empty comments, implausible timing, engagement composition and deleted/reposted patterns;
- measurement integrity: platform invalid-traffic signals and reconciliation differences.

Keep reason codes and observable evidence. The MRC invalid-traffic framework provides a useful distinction between valid human activity and activity that lacks the expected quality, completeness or legitimate source. Peer-reviewed research shows that synchronized following and follow-back patterns can identify coordinated inflation in studied datasets, but labeled real-world truth remains limited and high recall is difficult. ([MRC Invalid Traffic Addendum](https://www.mediaratingcouncil.org/sites/default/files/Standards/IVT%20Addendum%20Update%20062520.pdf); [Pacheco et al., 2024](https://doi.org/10.1140/epjds/s13688-024-00499-6); [Khosla et al., 2024](https://ojs.aaai.org/index.php/ICWSM/article/view/31321))

### Portfolio planning

The first useful product is a scenario builder. It should compare a few rosters under changed budget, overlap, expected response, risk and timing assumptions and show which constraints bind. Include a holdout or learning allocation where feasible. A formal optimizer can later maximize a declared expected objective under constraints, but it must never obscure uncertain inputs or the possibility that expected response was estimated from confounded history.

Academic influence-maximization and multi-criteria selection methods are useful algorithmic references. Much of the literature depends on known or simulated networks, stable diffusion, known costs or engineered preference weights, which rarely match creator campaigns. Validate any optimizer through retrospective replay followed by prospective controlled use, and report robust alternatives when parameter ranges change the recommended roster. ([Perrault et al., 2020](https://proceedings.mlr.press/v119/perrault20a/perrault20a.pdf); [Jiang et al., 2024](https://doi.org/10.1016/j.jik.2024.100502))

## Campaign planning, content and trends

### Planning before execution

Freeze a versioned campaign brief before performance data arrive. It should define the decision, target population, intervention, comparison, primary outcome and horizon; channel and creator roles; guardrails; tracking; minimum detectable effect and power where testing is planned; metric formulas; exclusions; stopping or decision rules; and who owns review.

Measure reach and frequency using source-appropriate definitions and segregate paid, organic and invalid activity. MRC notes that estimated reach often functions as a planning metric rather than direct observed evidence, so the product should preserve the source and estimation status. ([MRC Social Media Measurement Guidelines](https://mediaratingcouncil.org/sites/default/files/News/General-Announcements/MRC%20Social%20Measurement%20Guidelines%20v1.0%20Final.pdf))

### Content intelligence

Store observable content structure separately from inference:

- media segments, shots, duration and edit timing;
- caption, OCR and ASR text with timecodes and extraction confidence;
- visual subjects, product appearances, demonstrations, before/after structures and disclosure placement;
- audio/music/speech features and rights/source status where available;
- platform metadata and authorized retention/outcome observations;
- inferred hook, topic, beauty aspect, claim, sentiment, style or risk, each with evidence and method version.

Text-image embeddings such as CLIP are established tools for retrieval and zero-shot feature exploration, but benchmark generalization varies and embedding similarity is not a causal explanation. Use embeddings to find comparable content, cluster evidence and propose hypotheses; validate the named cluster and test performance claims experimentally. ([Radford et al., 2021](https://proceedings.mlr.press/v139/radford21a))

Owned-channel analytics can provide direct descriptive evidence. YouTube, for example, defines audience watch ratio and relative-retention metrics for authorized reports. TikTok Creative Center exposes top ads and trending hashtags, but it is a platform-curated view with an unspecified selection mechanism; it should seed discovery rather than define the market baseline. ([YouTube Analytics channel reports](https://developers.google.com/youtube/analytics/channel_reports); [YouTube Analytics metrics](https://developers.google.com/youtube/analytics/metrics); [TikTok Creative Center](https://ads.tiktok.com/resources/help/article/creative-center))

The final 2025 IAB/MRC attention guidelines cover signal-based, visual/audio tracking, physiological/neurological and panel/survey approaches. They require empirical validation when attention is modeled and warn against treating attention as a standalone effectiveness or business outcome. A product can support standardized attention metadata and evidence today; a universal cross-platform attention score is premature. ([IAB/MRC Attention Measurement Guidelines](https://www.mediaratingcouncil.org/sites/default/files/Standards/IAB_MRC_Attention_Measurement_Guidelines_November_2025.pdf))

## Brand safety, suitability and regulatory review

Separate four judgments:

1. **Brand safety:** whether content crosses a broadly unacceptable risk floor.
2. **Brand suitability:** whether otherwise permitted content fits this brand, product, audience and campaign.
3. **Commercial disclosure:** whether the material connection is represented as required for the market, platform and format.
4. **Product claims:** whether statements and demonstrations are permitted and substantiated for the product category and jurisdiction.

IAB Tech Lab’s Content Taxonomy supplies a maintained common language for content classification; its current page lists Content Taxonomy 3.1 and the earlier 3.0 release. GARM’s Brand Safety Floor and Suitability Framework remains a useful historical taxonomy reference, but the World Federation of Advertisers discontinued GARM in August 2024; the product should not present it as an active governing body. ([IAB Tech Lab Content Taxonomy](https://iabtechlab.com/standards/content-taxonomy/); [archived GARM framework](https://www.brandsafetyinstitute.com/resources/frameworks/brand-safety-floor-suitability); [WFA discontinuation notice](https://wfanet.org/knowledge/item/2024/08/09/wfa-discontinues-garm))

Platform controls differ in coverage and terminology. Google describes a safety baseline plus three inventory levels and discloses limits in placement coverage; TikTok describes three suitability tiers and machine-learning classification. These official documents show capabilities and configuration, but independent validation is needed for error rates and cross-platform comparability. ([Google Ads content suitability](https://support.google.com/google-ads/answer/12764663); [TikTok brand safety and suitability](https://ads.tiktok.com/business/en-US/brand-safety-suitability); [TikTok Brand Safety Hub](https://ads.tiktok.com/help/article/about-brand-safety-hub?lang=en))

The review object should contain jurisdiction, effective date, policy version, content evidence/timecode, subject, reason code, severity, automated result, reviewer decision, expiry/recheck rule and appeal/correction history. Keep policy rules outside the core ontology so they can change without redefining `Content`, `Creator` or `Campaign`.

## Measurement, attribution and causal learning

### A practical evidence ladder

1. **Validated descriptive reporting:** stable delivery, exposure, engagement and outcome definitions; deduplicated where the source permits; reconciled paid/organic and source differences.
2. **Deterministic path/accounting evidence:** UTM, code, affiliate, click/view, pixel and server-event reports under explicit attribution windows and identity coverage.
3. **Randomized lift:** individual/user-level randomization or platform conversion/brand-lift experiments where feasible.
4. **Randomized geo tests:** useful when individual assignment or outcome linkage is unavailable and enough independent markets exist.
5. **Quasi-experimental counterfactuals:** matched markets, synthetic controls, interrupted time series or Bayesian structural time series when randomization is infeasible and assumptions can be defended.
6. **Calibrated marketing-mix models:** channel-level, longer-horizon contribution and budget scenarios, preferably informed by experiments and reported as distributions.

These methods answer different estimands. Triangulate them; do not average them into a single unqualified “true ROI.”

### Attribution is accounting under a rule

Attribution is still useful for operations: codes and affiliate links can reconcile creator payments; UTMs and events can diagnose funnel loss; multi-touch rules can show sensitivity to the allocation model. Report unattributed outcomes, duplicate/missing identity, consent limitations, lookback windows, refunds/cancellations and platform-versus-first-party reconciliation.

Observational attribution can be badly biased because people likely to buy are also more likely to be exposed. Across 15 large Facebook advertising experiments, common observational methods often failed to reproduce randomized estimates even with rich data, which is strong evidence against treating adjusted attribution as incrementality. ([Gordon et al., 2019](https://gwern.net/doc/statistics/causality/2019-gordon.pdf))

### Randomized experiments

Predeclare the unit of randomization, eligibility population, primary outcome, horizon, minimum detectable effect, analysis method and interference risks. Use intention-to-treat as the default causal estimate; treatment-on-treated requires additional assumptions. Check assignment balance, attrition, treatment compliance, contamination and whether outcome collection differs by arm.

Official platform lift products implement randomized treatment/control designs. Google describes user- and geography-based Conversion Lift and reports incremental conversions/value and incremental CPA/ROAS; TikTok describes randomized Conversion Lift using pixel, Events API or mobile-measurement-partner outcomes. These documents establish the available mechanism. Any vendor benchmark claiming typical lift remains a vendor claim, and opaque eligibility, identity and analysis rules should be recorded. ([Google Conversion Lift](https://support.google.com/google-ads/answer/12003020?hl=en); [Google on attributed versus incremental conversions](https://support.google.com/google-ads/answer/14102450?hl=en-GB); [TikTok Conversion Lift](https://ads.tiktok.com/business/en-GB/blog/conversion-lift-study))

Brand-lift surveys add solicitation and response-selection risk, even with randomized exposure eligibility. Google’s research description explicitly distinguishes intended from actual treatment and discusses these biases. ([Google, Methods for Measuring Brand Lift](https://research.google/pubs/methods-for-measuring-brand-lift-of-online-ads/))

Power is a product feature, not an afterthought. Sales outcomes have high variance and advertising effects are often small; a campaign with millions of events can still be underpowered for incremental sales. The platform should compute power/MDE before promising an answer and label inconclusive tests accordingly. ([Lewis and Rao, 2015/2016](https://pubsonline.informs.org/doi/10.1287/mksc.2016.0998))

### Geo and quasi-experiments

Randomized geo experiments can estimate incremental impact where markets are sufficiently independent and treatment can be assigned geographically. Matched-market approaches are alternatives when exact randomization is unavailable, while synthetic controls construct a counterfactual from weighted controls. Always inspect pre-treatment fit, spillovers, simultaneous promotions, market shocks, placebo periods and sensitivity to donor-market inclusion. ([Google geo experiments](https://research.google/pubs/measuring-ad-effectiveness-using-geo-experiments/); [Google time-based regression matched markets](https://research.google/pubs/a-time-based-regression-matched-markets-approach-for-designing-geo-experiments/); [Meta GeoLift methodology](https://facebookincubator.github.io/GeoLift/docs/Methodology/))

Bayesian structural time-series methods can estimate a counterfactual after an intervention, but causal interpretation depends on stable relationships and unaffected controls. A credible interval from such a model expresses uncertainty conditional on the model; it does not prove those assumptions. ([Brodersen et al., 2015](https://kaybrodersen.github.io/publications/Brodersen_2015_AOAS.pdf))

### Marketing-mix modeling

MMM is best suited to aggregate channel contribution, carryover/saturation and budget scenarios over a sufficiently varied history. Bayesian models can express posterior uncertainty and include prior knowledge, but limited variation makes ROI weakly identified and priors influential. Report predictive checks, holdouts, alternate priors/specifications, saturation and carryover ranges, and whether experiments calibrated the response. ([Jin et al., 2017](https://research.google/pubs/bayesian-methods-for-media-mix-modeling-with-carryover-and-shape-effects/); [Google Meridian causal assumptions](https://developers.google.com/meridian/docs/causal-inference/intro); [Meridian experiment calibration](https://developers.google.com/meridian/docs/advanced-modeling/roi-priors-and-calibration))

Meta’s Robyn combines ridge regression, evolutionary optimization, adstock/saturation and experimental calibration, but its own documentation describes the package as experimental. It is an implementation option, not proof that a fitted decomposition is causal. ([Robyn repository](https://github.com/facebookexperimental/Robyn/blob/main/README.md); [Robyn features](https://facebookexperimental.github.io/Robyn/docs/features/))

## South Korea and Japan beauty extensions

### Shared beauty-domain concepts

Keep these as extensions to a cross-industry core:

- product, variant/shade and product category;
- ingredient and highlighted ingredient;
- skin/hair concern, routine step, application context and target user;
- sensory/appearance aspects such as shade, texture, finish, scent, staying power and packaging;
- claim, claim type, exact wording/timecode, product category, evidence and substantiation status;
- demonstration/before-and-after evidence and editing/context disclosures;
- commercial relationship, consideration type, disclosure text/placement/language and evidence;
- jurisdiction, rule/policy version, effective date and reviewer disposition.

Do not infer a person’s health condition from appearance. Keep cosmetics, functional cosmetics/quasi-drugs and medicines distinct because allowed claims and review paths differ.

### South Korea

Korea Fair Trade Commission materials document enforcement against advertisers that failed to disclose benefits provided to influencers. Its format-specific guidance has required disclosures to be conspicuous and expressed in the same language as the endorsement, with placement rules varying across images, video and text. Because these guides have changed, the platform should store the exact effective version and route edge cases for current local review. ([KFTC English enforcement summary](https://www.ftc.go.kr/eng/contents.do?key=557); [KFTC media-specific guidance, Korean](https://www.ftc.go.kr/www/selectBbsNttView.do?bordCd=1&key=5&nttSn=33198&pageIndex=9&pageUnit=10&searchCnd=all&searchCtgry=2))

The Ministry of Food and Drug Safety prohibits cosmetics advertising that can be mistaken for a medicine, exceeds approved functional-cosmetic claims, is false or misleading, or lacks substantiation for factual claims. MFDS publishes updated cosmetics advertising guidance and a 2024 guide to substantiation test methods, which should be linked to the policy version rather than copied permanently into model prompts. ([MFDS cosmetics labeling/advertising](https://www.mfds.go.kr/wpge/m_646/de050601l0025.do); [MFDS current advertising guide page](https://www.mfds.go.kr/brd/m_1060/view.do?company_cd=&company_nm=&itm_seq_1=0&itm_seq_2=0&multi_itm_seq=0&page=69&seq=15456&srchFr=&srchTo=&srchTp=&srchWord=); [MFDS substantiation test-method guide, 2024](https://www.mfds.go.kr/brd/m_1060/view.do?Data_stts_gubun=C1006&company_cd=&company_nm=&itm_seq_1=0&itm_seq_2=0&multi_itm_seq=0&page=1&seq=15567&srchFr=&srchTo=&srchTp=0&srchWord=))

Operational implications:

- evaluate Korean text, spacing variants, slang, transliteration and mixed Korean/English product names on an in-domain set;
- capture disclosure placement by frame/timecode as well as text;
- link every benefit/ingredient/clinical-looking statement to product category and evidence;
- separate an observed creator statement from the brand’s approved claim and reviewer decision.

### Japan

Japan’s Consumer Affairs Agency states that stealth marketing is regulated under the Act against Unjustifiable Premiums and Misleading Representations from 1 October 2023, with the advertiser as the regulated party. Preserve who directed or determined the representation and the evidence of the material relationship rather than inspecting hashtag text alone. ([CAA stealth-marketing FAQ, Japanese](https://www.caa.go.jp/policies/policy/representation/fair_labeling/faq/stealth_marketing/); [CAA 2026 English booklet](https://www.caa.go.jp/en/about_us/booklet/assets/pamphlet_en_2026_0000.pdf))

Japan’s MHLW advertising standard restricts misleading ingredient presentations, guarantees/superlatives and efficacy expressions outside the permitted category. A March 2025 notice adds guidance on highlighting specific ingredients, including stating their purpose, avoiding a medicinal impression, and making video qualifications legible. The Japan Cosmetic Industry Association also maintains a self-regulatory advertising guide. Cosmetics and quasi-drugs must remain separate product types. ([MHLW advertising regulation](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/koukokukisei/index.html); [MHLW proper advertising standard](https://www.mhlw.go.jp/web/t_doc?dataId=00ta6991&dataType=1&pageNo=1); [MHLW specific-ingredient notice, 2025](https://www.mhlw.go.jp/web/t_doc?dataId=00tc9762&dataType=1&pageNo=1); [JCIA advertising guidance](https://www.jcia.org/user/business/advertising/?o=JP1870%2F); [PMDA product-category FAQ](https://www.pmda.go.jp/english/about-pmda/0004.html))

Operational implications:

- evaluate Japanese scripts, emoji, omitted subjects, politeness, slang, transliteration and mixed-script brand/product names;
- represent cosmetic versus quasi-drug status and the permitted-claim source;
- detect ingredient emphasis and preserve nearby purpose/qualification text and video legibility evidence;
- route efficacy, safety, before/after and superlative claims to a market-aware reviewer.

## Product and ontology implications

The proposal’s separation of source observations, normalized/canonical knowledge, an operational ontology and rebuildable projections fits the evidence requirements. The analytical layer should extend it with a small set of governed concepts rather than flattening results onto Creator, Content or Campaign properties.

Recommended cross-industry concepts:

- `SourceCoverage`: source, access method, eligible surfaces, query, time interval, outage/limit and deletions policy.
- `MetricDefinition`: numerator, denominator, unit, eligibility, deduplication, attribution window, currency and version.
- `MetricObservation`: subject, value, window, source, definition and quality state.
- `AnalyticalEstimate`: decision/estimand, target population, method/model version, estimate or label, uncertainty semantics, evaluation evidence and limitations.
- `EvidenceArtifact`: source record, media segment, query snapshot, label set, experiment output or review evidence.
- `MeasurementPlan`: objective hierarchy, primary/secondary outcomes, instruments, experiment/power plan and decision rule.
- `Experiment`: assignment, treatment/control, population, outcomes, analysis and validity checks.
- `CreatorCandidate` and `CreatorPortfolioScenario`: eligibility, evidence components, constraints, assumptions and human decision.
- `RiskAssessment`: policy/version, evidence, reason/severity, automated result, review and expiry.
- `Disclosure`: material relationship, consideration, text/placement/language, format and evidence.
- `Claim` and `ClaimEvidence`: exact content statement, subject/product category, jurisdiction, substantiation and reviewer disposition.
- `LearningRecord`: frozen decision context, expected result, observed outcomes, interpretation, contradiction and next test.

Preserve `Creator` as a real person/organization and `PlatformAccount` as a platform-specific identity. A score, risk, trend or estimate should link to the subject and evidence; it should not become an unversioned timeless property of that subject.

### Model and LLM boundary

Use deterministic code for metric formulas, policy routing, joins, time windows, experiment assignment/analysis and reproducible constraints. Use trained models for retrieval, extraction, classification, clustering and forecasting only after in-domain evaluation. LLMs can summarize cited evidence, propose query expansions, help label clusters and draft analyst narratives, but every factual statement should trace to observations or calculations.

NIST’s AI Risk Management Framework and generative-AI profile emphasize validity, reliability, transparency, privacy, bias, information integrity and confabulation risk. Apply them through held-out evaluations, versioned prompts/models, evidence-grounded generation, structured outputs, abstention, human review for material decisions and monitoring by language/market. ([NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework); [NIST Generative AI Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf))

## Recommended implementation sequence for a small team

1. **Foundation:** source/permission inventory, canonical identities, source coverage, metric dictionary, evidence/provenance, immutable method versions and review queues.
2. **First decision product:** brand/product listening plus creator discovery for one beauty market and a narrow platform set. Ship evidence-backed retrieval, aspect taxonomy, decomposed creator ranking, policy review and saved shortlists.
3. **Measurement contract:** campaign brief and measurement plan, first-party link/code/event reconciliation, outcome hierarchy and post-campaign learning record.
4. **Validation:** build Korean/Japanese in-domain labeled sets for retrieval, entity linking, aspects/sentiment, disclosure/claim routing and authenticity review; publish slice-level performance internally.
5. **Causal capability:** integrate or design lift tests where scale permits; add geo/quasi-experiment support only with diagnostics and power checks.
6. **Portfolio and MMM:** add scenario optimization and calibrated MMM after sufficient cost, overlap, outcome and experimental evidence exists.

Defer a universal influence score, generalized virality forecast, automatic compliance verdict, self-optimizing creator portfolio and unqualified cross-platform ROI. Each would compress materially different evidence or outrun the available ground truth.

## Evidence limits

- Social-platform APIs, measurement definitions and product availability can change; every connector and metric needs a versioned effective date.
- Official platform documentation is authoritative about its documented feature, but platform-provided benchmarks, model quality and marketing outcomes are vendor claims unless independently tested.
- Influencer-marketing research contains useful experiments and large meta-analyses, but platforms, cultures, formats, products and outcome definitions remain heterogeneous. Korean and Japanese beauty-specific causal evidence is much thinner than the general evidence base.
- Brand-safety and regulatory sources establish frameworks and rules, not a substitute for current local legal review. Automated extraction and classification can prioritize review but cannot certify compliance.
- Confidence intervals quantify uncertainty conditional on sampling/design/model assumptions. They do not account automatically for source undercoverage, misclassification, unobserved confounding, policy errors or concept drift.
- The newest 2025–2026 standards and research are relevant to a September 2026 design, but operational adoption and independent replication are necessarily less mature.
