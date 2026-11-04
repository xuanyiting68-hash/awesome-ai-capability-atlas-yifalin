#!/usr/bin/env python3
"""V1.7.6 local Mock gateway policy. No HTTP runtime, keys or paid execution.

A production backend MUST independently authenticate user/tenant, implement
consent, stronger PII redaction, audit logging, rate limits and hard billing
boundaries before allowing ANY network provider. This module does not provide it.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from provider_contract_v174 import (
    ContractError, MockProvider, OpenAICompatibleContract, RemoteExecutionDisabled,
    TaskRequest, ProviderReply, validate_citations,
)

EMAIL=re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?!\w)",re.I)
BEARER=re.compile(r"(?i)\b(?:Bearer\s+[A-Za-z0-9._~+/-]{8,}|sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,})")
# Heuristic checks reduce mistakes, but can never guarantee the absence of PII.
PHONE=re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)|(?<!\d)(?:\+?61[- ]?)?4\d{8}(?!\d)")

@dataclass(frozen=True)
class ResearchPolicy:
    allowed_provider: str = "mock"
    network_enabled: bool = False
    permitted_cost_usd: int = 0
    user_data_export_allowed: bool = False
    customer_data_allowed: bool = False
    max_input_chars: int = 400
    max_output_tokens: int = 384

    def validate(self) -> "ResearchPolicy":
        if (self.allowed_provider!="mock" or self.network_enabled is not False
                or type(self.permitted_cost_usd) is not int or self.permitted_cost_usd!=0
                or self.user_data_export_allowed is not False or self.customer_data_allowed is not False):
            raise RemoteExecutionDisabled("Atlas research branch: Mock only, USD 0 and zero egress")
        if type(self.max_input_chars) is not int or not 1<=self.max_input_chars<=400:
            raise ContractError("Input bound invalid")
        if type(self.max_output_tokens) is not int or not 1<=self.max_output_tokens<=512:
            raise ContractError("Output bound invalid")
        return self

def enforce_research_policy(request: TaskRequest, policy: ResearchPolicy) -> None:
    policy.validate()
    request.validate()
    text="\n".join([request.task]+[t.content for t in request.turns])
    if len(request.task)>policy.max_input_chars or request.max_output_tokens>policy.max_output_tokens:
        raise ContractError("Input or output cap exceeded")
    if EMAIL.search(text) or BEARER.search(text) or PHONE.search(text):
        raise ContractError("Potential personal/secret data detected; fail closed")
    # Never treat email/credential regex as a reliable customer-data classifier.

def local_reply(request: TaskRequest, policy: ResearchPolicy = ResearchPolicy()) -> ProviderReply:
    enforce_research_policy(request,policy)
    reply=MockProvider().generate(request)
    validate_citations(reply,request)
    if reply.billed_usd!=0 or reply.provider!="mock" or reply.mode!="offline-mock":
        raise ContractError("Provider boundary violated")
    return reply

def remote_reply_denied(request: TaskRequest, provider: str, policy: ResearchPolicy = ResearchPolicy()) -> None:
    # Even if a caller mistakenly constructs a remote envelope, no execution is possible.
    policy.validate()
    raise RemoteExecutionDisabled("Live network model dispatch is not implemented or authorised")

if __name__=="__main__":
    raise SystemExit("This file defines a zero-network Mock contract only.")
