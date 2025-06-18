from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Project:
    project_id: str  # Unique identifier for the project
    branch: str
    operations: str
    description: str
    depreciation_method: int  # Foreign key referencing depreciation_schedules(depreciation_id)
    cost_center: int  # Cost center for the project

@dataclass
class ProjectClassification:
    project_id: str  # Foreign key to bind with Project
    importance: int  # Importance level of the project (e.g., 1 for High, 2 for Medium, 3 for Low)
    type: int  # Type of the project (e.g., 1 for Infrastructure, 2 for IT, etc.)

@dataclass
class Investment:
    project_id: str  # Foreign key to bind with Project
    yearly_investments: Dict[int, float] = field(default_factory=dict)
    depreciation_start_years: Dict[int, int] = field(default_factory=dict)  # Maps investment years to their depreciation start years

@dataclass
class DepreciationSchedule:
    depreciation_id: str  # Unique identifier for the depreciation schedule
    schedule: Dict[int, str] = field(default_factory=dict)
    depreciation_percentage: float = 0.0  # Percentage to depreciate remaining value each year
    depreciation_years: int = 0  # Number of years for depreciation
    method_description: str = ""  # Description of the depreciation method

@dataclass
class CalculatedDepreciation:
    project_id: str  # Foreign key to bind with Project
    calculated_values: Dict[int, float] = field(default_factory=dict)