# Pydantic models for input parsing
from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field

IssueStatus = Literal["open", "closed", "in_review", "pending", "draft","is_pending","completed","not_approved","in_dispute"]
ReviewStatus = Literal["open", "closed", "void"]
FormStatus = Literal["closed","in_progress","in_review"]
Intent = Literal["get_issues", "get_reviews", "get_forms"]

class IssueParams(BaseModel):
    """Parameters for querying issues."""
    intent: Literal["get_issues"] = "get_issues"
    assignee_name: Optional[str] = Field(None, description="Name of the person the issue is assigned to. Use 'current_user' for the user making the query.")
    project_name: Optional[str] = Field(None, description="Name of the project the issue belongs to.")
    issue_status: Optional[List[IssueStatus]] = Field(default_factory=list, description="The current status of the issue (e.g., open, closed).")
    due_date: Optional[str] = Field(None, description="The due date, can be a specific date 'YYYY-MM-DD' or a relative term like 'today', 'tomorrow', 'next_week' or a range")
    issue_type: Optional[List[str]] = Field(default_factory=list, description="The category or type of the issue, e.g., 'Safety', 'Quality'.")
    count_only: bool = Field(False, description="Set to true if the user only asks for the number/count of items.")

class ReviewParams(BaseModel):
    """Parameters for querying reviews."""
    intent: Literal["get_reviews"] = "get_reviews" 
    project_name: Optional[str] = Field(None, description="Name of the project the review belongs to.")
    assignee_name: Optional[str] = Field(None, description="Name of the person the issue is assigned to. Use 'current_user' for the user making the query.")
    review_status: Optional[List[ReviewStatus]] = Field(default_factory=list, description="The current status of the review (e.g., open, closed).")
    due_date: Optional[str] = Field(None, description="The due date, can be a specific date 'YYYY-MM-DD' or a relative term like 'today', 'tomorrow', 'next_week' or a range")
    step_number: Optional[int] =Field(None, description="the step at which the review is currently at 1,2,3,4")
    review_workflow: Optional[List[str]] = Field(default_factory=list, description="The specific name of the review workflow. This often follows a pattern like 'Prefix.Stage-Name'. For example: 'S1.S3-Architecture', 'WP.S1-Structure'. The user might refer to this as a 'workflow', 'process', or 'review type'.")
    count_only: bool = Field(False, description="Set to true if the user only asks for the number/count of items.")

class FormParams(BaseModel):
    """Parameters for querying forms."""
    intent: Literal["get_forms"] = "get_forms" 
    project_name: Optional[str] = Field(None, description="Name of the project the form belongs to.")
    assignee_name: Optional[str] = Field(None, description="Name of the person the issue is assigned to. Use 'current_user' for the user making the query.")
    created_on: Optional[str] = Field(None, description="The date on which the form is created, can be a specific date 'YYYY-MM-DD' or a relative term like 'today', 'tomorrow', 'next_week' or a range")
    form_status: Optional[List[FormStatus]] = Field(default_factory=list, description="The current status of the form (e.g., open, draft).")
    form_template: Optional[List[str]] = Field(default_factory=list, description="The form template name of the form, e.g., 'CVL.QC-Concrete Abstract', 'WIR'.")
    count_only: bool = Field(False, description="Set to true if the user only asks for the number/count of items.")

ParametersUnion = Union[IssueParams, ReviewParams, FormParams]

