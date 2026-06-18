from app.models.user import User
from app.models.config import (
    CfgRegion,
    CfgCustomerType,
    CfgLeadSource,
    CfgContactRole,
    CfgTaskTemplate,
    CfgStage,
    CfgStageProbability,
    CfgOpportunityType,
    CfgLostReason,
    CfgClientMentalState,
    CfgAiPrompt,
)
from app.models.account import Account, Contact, ContactChannel
from app.models.opportunity import Opportunity, Task, Activity
from app.models.target import Target
from app.models.audit import AuditLog, AppVersion
from app.models.feedback import UserFeedback
from app.models.material import MaterialDocument
from app.models.email_template import EmailTemplate, EmailSent
from app.models.comunicacion import Publicacion, Desarrollo, SalidaCanal

__all__ = [
    # Users
    "User",
    # Config
    "CfgRegion",
    "CfgCustomerType",
    "CfgLeadSource",
    "CfgContactRole",
    "CfgTaskTemplate",
    "CfgStage",
    "CfgStageProbability",
    "CfgOpportunityType",
    "CfgLostReason",
    "CfgClientMentalState",
    "CfgAiPrompt",
    # Accounts & Contacts
    "Account",
    "Contact",
    "ContactChannel",
    # Opportunities, Tasks, Activities
    "Opportunity",
    "Task",
    "Activity",
    # System
    "Target",
    "AuditLog",
    "AppVersion",
    "UserFeedback",
    "MaterialDocument",
    "EmailTemplate",
    "EmailSent",
    "Publicacion",
    "Desarrollo",
    "SalidaCanal",
]
