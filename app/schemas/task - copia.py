"""
Pydantic schemas for Task
"""
from pydantic import BaseModel, Field
from typing import Optional


class TaskBase(BaseModel):
    """Base task schema"""
    opportunity_id: str
    task_template_id: Optional[str] = None
    title: str = Field(..., min_length=1)
    due_date: Optional[str] = None  # ISO date format
    assigned_to_user_id: Optional[str] = None


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    task_template_id: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1)
    due_date: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(open|done|canceled)$")
    assigned_to_user_id: Optional[str] = None


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: str
    opportunity_id: str
    task_template_id: Optional[str] = None
    title: str
    due_date: Optional[str] = None
    status: str
    assigned_to_user_id: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for list of tasks"""
    tasks: list[TaskResponse]
    total: int
