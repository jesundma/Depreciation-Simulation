from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Project:
    project_id: str
    branch: str
    operations: str
    description: str

@dataclass
class Investment:
    yearly_investments: Dict[int, float] = field(default_factory=dict)

@dataclass
class DepreciationSchedule:
    schedule: Dict[int, str] = field(default_factory=dict)

@dataclass
class CalculatedDepreciation:
    calculated_values: Dict[int, float] = field(default_factory=dict)