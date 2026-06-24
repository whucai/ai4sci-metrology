"""Paper registry and IMRaD section splitter."""

from .registry import (
    PAPER_REGISTRY,
    ALL_CLAIMS,
    METRIC_TYPE_MAP,
    READY_PAPERS,
    PENDING_PAPERS,
    get_paper,
    get_papers_by_metric,
    get_all_paper_ids,
    get_all_claims,
)
from .sections import split_paper_sections, enrich_paper_entry
