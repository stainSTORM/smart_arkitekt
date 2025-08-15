"""
Smart Arkitekt Multi-Device Workflow Orchestrator

A minimal, testable state-machine that executes slide workflows across
three devices (Robot Arm, Opentrons, Microscope) with live visualization
and Arkitekt integration hooks.

Example usage:
    from smart_arkitekt import build_demo
    
    orchestrator = build_demo(max_wash_loops=2)
    orchestrator.run([1, 2, 3, 4])
"""

from .orchestrator import Orchestrator, build_demo
from .models import Station, Slide
from .robot_arm import RobotArm
from .opentrons import Opentrons  
from .microscope import Microscope
from .image_processor import ImageProcessor
from .visualizer import (
    MatplotlibVisualizer,
    ConsoleVisualizer,
    create_visualizer
)

__version__ = "1.0.0"
__author__ = "Smart Arkitekt Team"

__all__ = [
    # Core workflow components
    "Station",
    "Slide", 
    "RobotArm",
    "Opentrons", 
    "Microscope",
    "ImageProcessor",
    "Orchestrator",
    "build_demo",
    
    # Visualization components
    "MatplotlibVisualizer",
    "ConsoleVisualizer", 
    "create_visualizer",
]