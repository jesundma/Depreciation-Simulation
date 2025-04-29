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

@dataclass
class DepreciationSchedule:
    project_id: str  # Foreign key to bind with Project
    schedule: Dict[int, str] = field(default_factory=dict)

@dataclass
class CalculatedDepreciation:
    project_id: str  # Foreign key to bind with Project
    calculated_values: Dict[int, float] = field(default_factory=dict)