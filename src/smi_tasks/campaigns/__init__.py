"""Save-first application composition for campaign recommendations and discovery."""

from smi_campaigns import CampaignStore
from smi_ingestion.evidence_sets import ActorContext

from ..store import AcquisitionTasks


class CampaignRecommendations:
    """Return a durable supported result independently of enrichment admission."""

    def __init__(self, campaigns: CampaignStore, tasks: AcquisitionTasks):
        self.campaigns, self.tasks = campaigns, tasks

    def recommend(self, campaign_id: str, brief_id: str, actor: ActorContext, *, ranked: bool = False, **options) -> dict:
        """Save through the campaign owner, then admit that exact coverage need.

        Retrying the same request reopens the saved decision before task admission;
        the shortlist identity also owns retries after interruption between commits.
        """
        operation = self.campaigns.recommend_ranked if ranked else self.campaigns.recommend
        saved = operation(campaign_id, brief_id, actor, **options)
        if saved.get('shortlist_id'):
            self.tasks.submit_campaign_discovery(saved['shortlist_id'], actor, include_synthetic=options.get('include_synthetic', False))
        return saved

    def read(self, shortlist_id: str, actor: ActorContext, *, include_synthetic: bool = False) -> dict:
        """Reopen the immutable shortlist with current enrichment progress."""
        return {'shortlist': self.campaigns.read_shortlist(shortlist_id, actor, include_synthetic=include_synthetic),
                'enrichment': self.tasks.read_campaign_discovery(shortlist_id, actor)}
