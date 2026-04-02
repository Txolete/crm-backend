"""
Pydantic schemas for Task
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date


class TaskBase(BaseModel):
    """Base task schema"""
    opportunity_id: Optional[str] = None
    account_id: Optional[str] = None
    task_template_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None  # ISO date YYYY-MM-DD, Pydantic parses strings
    priority: str = Field(default='medium', pattern="^(high|medium|low)$")
    assigned_to_user_id: Optional[str] = None
    reminder_date: Optional[datetime] = None

    @field_validator('opportunity_id', 'account_id')
    @classmethod
    def validate_link(cls, v, info):
        """Al menos opportunity_id o account_id debe estar presente"""
        # Esta validación se hará en el endpoint, aquí solo definimos los campos
        return v


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    opportunity_id: Optional[str] = None
    account_id: Optional[str] = None
    task_template_id: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    status: Optional[str] = Field(None, pattern="^(open|in_progress|completed|cancelled)$")
    assigned_to_user_id: Optional[str] = None
    reminder_date: Optional[datetime] = None


class TaskComplete(BaseModel):
    """Schema for completing a task"""
    completed_by_user_id: str


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: str
    opportunity_id: Optional[str] = None
    account_id: Optional[str] = None
    task_template_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: str
    status: str
    assigned_to_user_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    completed_by_user_id: Optional[str] = None
    reminder_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskWithRelations(TaskResponse):
    """Task with related entity names for UI"""
    task_template_name: Optional[str] = None
    opportunity_name: Optional[str] = None
    account_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    completed_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for list of tasks"""
    tasks: list[TaskWithRelations]
    total: int
