"""
Task schemas - PASO 8
"""
from pydantic import BaseModel
from typing import List


# PASO 8 - Tasks Overview (Semáforo)

class TaskOverviewItem(BaseModel):
    task_id: str
    title: str
    due_date: str
    opportunity_id: str
    account_name: str
    stage_key: str
    stage_name: str


class TasksOverviewResponse(BaseModel):
    overdue: List[TaskOverviewItem]
    due_soon: List[TaskOverviewItem]
    upcoming: List[TaskOverviewItem]
    total_overdue: int
    total_due_soon: int
    total_upcoming: int
