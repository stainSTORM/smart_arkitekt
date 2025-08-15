"""
Domain models for the workflow orchestrator.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

class Station(Enum):
    """Available stations in the workflow"""
    RACK = auto()
    ROBOT = auto() 
    OPENTRONS = auto()
    MICROSCOPE = auto()
    IMAGE_PROCESSOR = auto()
    DROPOFF = auto()

@dataclass
class Slide:
    """Represents a slide being processed"""
    id: int
    loop_count: int = 0
    is_ok: Optional[bool] = None
    image_analysis_complete: bool = False