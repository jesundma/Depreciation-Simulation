from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Project:
    project_id: str  # Unique identifier for the project
    branch: str
    operations: str
    description: str

@dataclass
class Investment:
    project_id: str  # Foreign key to bind with Project
    yearly_investments: Dict[int, float] = field(default_factory=dict)
    depreciation_start_years: Dict[int, int] = field(default_factory=dict)  # Maps investment years to their depreciation start years

@dataclass
class DepreciationSchedule:
    project_id: str  # Foreign key to bind with Project
    schedule: Dict[int, str] = field(default_factory=dict)
    depreciation_percentage: float = 0.0  # Percentage to depreciate remaining value each year
    depreciation_years: int = 0  # Number of years for depreciation
    method_description: str = ""  # Description of the depreciation method

@dataclass
class CalculatedDepreciation:
    project_id: str  # Foreign key to bind with Project
    calculated_values: Dict[int, float] = field(default_factory=dict)