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

from .workflow_orchestrator import (
    Station,
    Slide, 
    RobotArm,
    Opentrons,
    Microscope,
    Orchestrator,
    build_demo
)

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
    "Orchestrator",
    "build_demo",
    
    # Visualization components
    "MatplotlibVisualizer",
    "ConsoleVisualizer", 
    "create_visualizer",
]