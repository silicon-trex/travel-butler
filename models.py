from pydantic import BaseModel
from typing import List, Optional


class PlanRequest(BaseModel):
    destination: str
    start_date: str
    days: int
    group: str
    pace: str
    interest: str
    budget: str


class EmergencyRequest(BaseModel):
    scenario: str


class AgentStatusMsg(BaseModel):
    type: str = "agent_status"
    agent_id: int
    state: str
    detail: str = ""


class LogMsg(BaseModel):
    type: str = "log"
    agent_name: str
    message: str
    log_type: str = "info"


class TokenUpdateMsg(BaseModel):
    type: str = "token_update"
    count: int


class PlanResultMsg(BaseModel):
    type: str = "plan_result"
    data: dict


class EmergencyResultMsg(BaseModel):
    type: str = "emergency_result"
    data: dict


class PriceUpdateMsg(BaseModel):
    type: str = "price_update"
    data: list


class ErrorMsg(BaseModel):
    type: str = "error"
    message: str


class DoneMsg(BaseModel):
    type: str = "done"
