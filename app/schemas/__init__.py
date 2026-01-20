"""
Pydantic schemas
"""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResetPassword,
    UserResponse,
    UserListResponse
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse
)
from app.schemas.account import (
    AccountBase,
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountListResponse
)
from app.schemas.contact import (
    ContactBase,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListResponse,
    ContactChannelBase,
    ContactChannelCreate,
    ContactChannelUpdate,
    ContactChannelResponse
)
from app.schemas.opportunity import (
    OpportunityBase,
    OpportunityCreate,
    OpportunityUpdate,
    OpportunityCloseRequest,
    OpportunityResponse,
    OpportunityListResponse
)
from app.schemas.task import (
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse
)
from app.schemas.activity import (
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
    ActivityListResponse
)
from app.schemas.kanban import (
    KanbanNextTask,
    KanbanBadges,
    KanbanOwner,
    KanbanOpportunityItem,
    KanbanStage,
    KanbanColumn,
    KanbanResponse,
    MoveStageRequest,
    MoveStageResponse,
    CloseOpportunityRequest,
    CloseOpportunityResponse
)
from app.schemas.dashboard import (
    DashboardFilters,
    DashboardTargets,
    DashboardKPIs,
    DashboardSeries,
    BreakdownItem,
    DashboardBreakdowns,
    DashboardSummaryResponse,
    TargetsResponse,
    TargetsUpdateRequest,
    TargetsUpdateResponse
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResetPassword",
    "UserResponse",
    "UserListResponse",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "LogoutResponse",
    "MeResponse",
    # Account
    "AccountBase",
    "AccountCreate",
    "AccountUpdate",
    "AccountResponse",
    "AccountListResponse",
    # Contact
    "ContactBase",
    "ContactCreate",
    "ContactUpdate",
    "ContactResponse",
    "ContactListResponse",
    "ContactChannelBase",
    "ContactChannelCreate",
    "ContactChannelUpdate",
    "ContactChannelResponse",
    # Opportunity
    "OpportunityBase",
    "OpportunityCreate",
    "OpportunityUpdate",
    "OpportunityCloseRequest",
    "OpportunityResponse",
    "OpportunityListResponse",
    # Task
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    # Activity
    "ActivityCreate",
    "ActivityUpdate",
    "ActivityResponse",
    "ActivityListResponse",
    # Kanban
    "KanbanNextTask",
    "KanbanBadges",
    "KanbanOwner",
    "KanbanOpportunityItem",
    "KanbanStage",
    "KanbanColumn",
    "KanbanResponse",
    "MoveStageRequest",
    "MoveStageResponse",
    "CloseOpportunityRequest",
    "CloseOpportunityResponse",
    # Dashboard
    "DashboardFilters",
    "DashboardTargets",
    "DashboardKPIs",
    "DashboardSeries",
    "BreakdownItem",
    "DashboardBreakdowns",
    "DashboardSummaryResponse",
    "TargetsResponse",
    "TargetsUpdateRequest",
    "TargetsUpdateResponse",
]
