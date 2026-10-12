"""Explicit adapter registration; the runner never branches on source format."""

from ..contracts import Collector, Mapper
from .bright_data import BrightDataTikTokCollector, BrightDataTikTokMapper
from .html_fixture import HtmlFixtureMapper
from .json_fixture import JsonFixtureMapper
from .local import LocalFileCollector
from .tiktok_oembed import TikTokOEmbedCollector, TikTokOEmbedMapper
from .tiktok_web import TikTokWebCollector, TikTokWebMapper


class AdapterRegistry:
    def __init__(self):
        self._adapters: dict[str, tuple[Collector, Mapper]] = {}

    def register(self, adapter_id: str, collector: Collector, mapper: Mapper) -> None:
        if adapter_id in self._adapters:
            raise ValueError("adapter_already_registered")
        self._adapters[adapter_id] = (collector, mapper)

    def resolve(self, adapter_id: str) -> tuple[Collector, Mapper]:
        try:
            return self._adapters[adapter_id]
        except KeyError as error:
            raise ValueError("unsupported_adapter") from error


def default_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register("fixture-json", LocalFileCollector("fixture-json"), JsonFixtureMapper())
    registry.register("fixture-html", LocalFileCollector("fixture-html"), HtmlFixtureMapper())
    registry.register("tiktok-oembed", TikTokOEmbedCollector(), TikTokOEmbedMapper())
    registry.register("brightdata-tiktok", BrightDataTikTokCollector(), BrightDataTikTokMapper())
    registry.register("tiktok-web", TikTokWebCollector(), TikTokWebMapper())
    return registry
