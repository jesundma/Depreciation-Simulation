from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Project:
    project_id: str
    branch: str
    operations: str
    description: str
    yearly_investments: Dict[int, float] = field(default_factory=dict)
    depreciation_schedule: Dict[int, str] = field(default_factory=dict)
    calculated_depreciations: Dict[int, float] = field(default_factory=dict)