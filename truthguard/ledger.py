"""
TruthGuard Contradiction Ledger
Records detected contradictions between active policies, outdated FAQs, rogue emails, and overlapping contracts.
Ranks fix-it tickets by Priority = Traffic × Risk.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import uuid


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class ContradictionTicket(BaseModel):
    ticket_id: str = Field(default_factory=lambda: f"TICKET-{uuid.uuid4().hex[:6].upper()}")
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    winning_clause_id: str
    winning_doc_title: str
    conflicting_clause_id: str
    conflicting_doc_title: str
    trap_category: str
    traffic_weight: int = Field(default=50, description="Monthly query or page traffic score (1-100)")
    risk_level: int = Field(default=3, description="Risk factor (1=low to 5=critical financial/legal liability)")
    priority_score: int = Field(default=150, description="Traffic × Risk")
    doc_owner: str = Field(default="Content Ops")
    summary: str
    recommended_action: str
    status: TicketStatus = TicketStatus.OPEN


class ContradictionLedger:
    def __init__(self):
        self.tickets: Dict[str, ContradictionTicket] = {}

    def log_contradiction(
        self,
        winning_clause_id: str,
        winning_doc_title: str,
        conflicting_clause_id: str,
        conflicting_doc_title: str,
        trap_category: str,
        doc_owner: str,
        summary: str,
        recommended_action: str,
        traffic_weight: int = 60,
        risk_level: int = 4
    ) -> ContradictionTicket:
        # Check if already logged to avoid exact duplicates
        for ticket in self.tickets.values():
            if (
                ticket.winning_clause_id == winning_clause_id
                and ticket.conflicting_clause_id == conflicting_clause_id
                and ticket.trap_category == trap_category
            ):
                # Update traffic / bump
                return ticket

        priority_score = traffic_weight * risk_level
        ticket = ContradictionTicket(
            winning_clause_id=winning_clause_id,
            winning_doc_title=winning_doc_title,
            conflicting_clause_id=conflicting_clause_id,
            conflicting_doc_title=conflicting_doc_title,
            trap_category=trap_category,
            traffic_weight=traffic_weight,
            risk_level=risk_level,
            priority_score=priority_score,
            doc_owner=doc_owner,
            summary=summary,
            recommended_action=recommended_action,
            status=TicketStatus.OPEN
        )
        self.tickets[ticket.ticket_id] = ticket
        return ticket

    def get_ranked_tickets(self) -> List[ContradictionTicket]:
        """Returns all tickets sorted by Priority Score (traffic × risk) descending."""
        return sorted(self.tickets.values(), key=lambda t: t.priority_score, reverse=True)

    def update_status(self, ticket_id: str, new_status: TicketStatus):
        if ticket_id in self.tickets:
            self.tickets[ticket_id].status = new_status

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [t.model_dump() for t in self.get_ranked_tickets()]
