"""
TruthGuard Schema
Contract between extractor, graph, and precedence engine.
Conforms strictly to Section 3 of TruthGuard Implementation Plan.
"""

from __future__ import annotations
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, field_validator


class DocType(str, Enum):
    REGULATION = "regulation"
    BOARD_POLICY = "board policy"
    PRODUCT_TC = "product T&C"
    FAQ = "FAQ"
    SUPPORT_EMAIL = "support email"


class SpecificityType(str, Enum):
    NARROW = "narrow"
    GENERAL = "general"


class RelationType(str, Enum):
    AMENDS = "amends"
    WITHDRAWS = "withdraws"
    APPLIES_TO = "applies_to"
    SUPERSEDES = "supersedes"


# Authority Rank Table (Section 3: regulation > board policy > product T&C > FAQ > email)
# Can be swapped per industry (e.g. Telecom, Media Rights, Banking)
DEFAULT_AUTHORITY_TABLE: Dict[str, int] = {
    "regulation": 5,
    "board policy": 4,
    "product T&C": 3,
    "FAQ": 2,
    "support email": 1,
}

MEDIA_AUTHORITY_TABLE: Dict[str, int] = {
    "statutory law": 5,
    "master licensing agreement": 4,
    "distribution deal memo": 3,
    "press release / FAQ": 2,
    "sales rep email": 1,
}


class Scope(BaseModel):
    product: str = Field(default="all", description="Product category or plan, e.g. prepaid, postpaid, OTT-tier")
    region: str = Field(default="all", description="Region or territory, e.g. all, Delhi, Germany, UK")
    customer_segment: str = Field(default="all", description="Target segment, e.g. retail, enterprise, student, all")

    def matches(self, query_scope: Optional[Scope]) -> bool:
        """
        Check if this clause scope covers the queried customer scope.
        A clause with 'all' matches any query.
        If a clause has a specific region/product/segment, it only matches queries in that specific region/product/segment.
        """
        if not query_scope:
            return True

        # Region match: specific clause region only applies if query is in that specific region
        if self.region.lower() != "all":
            if query_scope.region.lower() != self.region.lower():
                return False

        # Product match: specific clause product only applies if query is for that product
        if self.product.lower() != "all":
            if query_scope.product.lower() != self.product.lower():
                return False

        # Customer segment match: specific segment only applies if query is in that segment
        if self.customer_segment.lower() != "all":
            if query_scope.customer_segment.lower() != self.customer_segment.lower():
                return False

        return True


class Relation(BaseModel):
    type: RelationType
    target: str = Field(description="Target clause_id that this relation points to")


class Clause(BaseModel):
    clause_id: str = Field(description="Unique, stable ID used in citations, e.g. RP-v1-4.2")
    doc_id: str = Field(description="Source document name / ID, e.g. Refund Policy v1")
    doc_type: str = Field(description="Source document type, e.g. board policy, FAQ")
    text: str = Field(description="The clause wording")
    authority_rank: int = Field(default=3, description="Rank from 1 (lowest) to 5 (highest)")
    scope: Scope = Field(default_factory=Scope)
    published_date: date = Field(description="When it was released")
    effective_from: date = Field(description="When it is actually in force")
    effective_to: Optional[date] = Field(default=None, description="When force ends, or None if currently open")
    relations: List[Relation] = Field(default_factory=list, description="amends, withdraws, applies_to links")
    specificity: SpecificityType = Field(default=SpecificityType.GENERAL, description="narrow vs general")
    topic: str = Field(default="general", description="Clause category, e.g. refund_window, payment_method, roaming_cap")

    @field_validator("published_date", "effective_from", mode="before")
    def parse_dates(cls, v: Any) -> date:
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            # Parse ISO or YYYY-MM-DD
            try:
                return datetime.strptime(v.strip(), "%Y-%m-%d").date()
            except ValueError:
                # Try month year or common format
                for fmt in ("%d %b %Y", "%b %Y", "%Y/%m/%d"):
                    try:
                        return datetime.strptime(v.strip(), fmt).date()
                    except ValueError:
                        pass
        raise ValueError(f"Unable to parse date string: {v}")

    @field_validator("effective_to", mode="before")
    def parse_effective_to(cls, v: Any) -> Optional[date]:
        if v is None or v == "" or v == "open" or v == "None":
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return datetime.strptime(v.strip(), "%Y-%m-%d").date()
            except ValueError:
                for fmt in ("%d %b %Y", "%b %Y", "%Y/%m/%d"):
                    try:
                        return datetime.strptime(v.strip(), fmt).date()
                    except ValueError:
                        pass
        return None

    def is_in_force_on(self, as_of_date: date) -> bool:
        """
        Check if clause is in force on the given as_of_date:
        effective_from <= as_of_date and (effective_to is None or as_of_date <= effective_to)
        """
        if as_of_date < self.effective_from:
            return False
        if self.effective_to is not None and as_of_date > self.effective_to:
            return False
        return True


class DocumentMetadata(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    published_date: date
    effective_from: date
    effective_to: Optional[date] = None
    industry: str = "telecom"
    owner: str = "Policy & Legal Ops"
    traffic_weight: int = Field(default=50, description="Monthly traffic estimate (1-100) for risk calculation")
    risk_level: int = Field(default=3, description="Risk multiplier from 1 (minor) to 5 (critical legal/financial liability)")
    clauses: List[Clause] = Field(default_factory=list)
