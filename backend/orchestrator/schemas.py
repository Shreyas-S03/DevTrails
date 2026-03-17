from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DisruptionPayload(BaseModel):
    type: str = Field(..., min_length=1)
    intensity_value: float = Field(..., ge=0.0)
    zone: str = Field(..., min_length=1)


class ClaimRequest(BaseModel):
    rider_id: str = Field(..., min_length=1)
    disruption: DisruptionPayload


class ClaimDecision(BaseModel):
    claim_status: Literal["APPROVED", "DENIED", "FRAUD_FLAGGED", "MANUAL_REVIEW"]
    payout_amount: float = Field(..., ge=0.0)
    reason: str
