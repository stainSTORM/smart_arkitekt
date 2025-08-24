"""
Robot Arm device implementation with explicit from->to movement methods.
"""

import time
from typing import Callable, Dict

class RobotArm:
    """
    Robot Arm with explicit movement methods indicating source and destination.
    All movements are from->to to make the workflow clear.
    """
    
    def __init__(self, emit: Callable[[str, Dict], None]): 
        self.emit = emit

    # Basic positioning
    def move_start_position(self):
        """Move robot to start/idle position"""
        self.emit("robot.move_start", {}); time.sleep(0.05)

    def move_pickup_position(self, slot: int):
        """Move to pickup position at specified slot"""
        self.emit("robot.move_pickup", {"slot": slot}); time.sleep(0.05)

    # Gripper control
    def close_gripper(self):
        """Close the gripper to grab slide"""
        self.emit("robot.close_gripper", {}); time.sleep(0.02)

    def open_gripper(self):
        """Open the gripper to release slide"""
        self.emit("robot.open_gripper", {}); time.sleep(0.02)

    # Explicit from->to movements
    def move_from_rack_to_opentrons(self, slide_id: int, opentrons_slot: int):
        """Move slide from rack to opentrons"""
        self.emit("robot.move_rack_to_opentrons", {
            "slide": slide_id, 
            "opentrons_slot": opentrons_slot
        }); time.sleep(0.1)

    def move_from_opentrons_to_microscope(self, slide_id: int, opentrons_slot: int):
        """Move slide from opentrons to microscope"""
        self.emit("robot.move_opentrons_to_microscope", {
            "slide": slide_id,
            "opentrons_slot": opentrons_slot
        }); time.sleep(0.1)

    def move_from_microscope_to_opentrons(self, slide_id: int, opentrons_slot: int):
        """Move slide from microscope back to opentrons for washing"""
        self.emit("robot.move_microscope_to_opentrons", {
            "slide": slide_id,
            "opentrons_slot": opentrons_slot
        }); time.sleep(0.1)

    def move_from_microscope_to_image_processor(self, slide_id: int):
        """Move slide from microscope to image processor"""
        self.emit("robot.move_microscope_to_image_processor", {
            "slide": slide_id
        }); time.sleep(0.1)

    def move_from_image_processor_to_dropoff(self, slide_id: int, dropoff_slot: int):
        """Move slide from image processor to dropoff"""
        self.emit("robot.move_image_processor_to_dropoff", {
            "slide": slide_id,
            "dropoff_slot": dropoff_slot
        }); time.sleep(0.1)

    def move_from_microscope_to_dropoff(self, slide_id: int, dropoff_slot: int):
        """Move slide directly from microscope to dropoff (for failed slides)"""
        self.emit("robot.move_microscope_to_dropoff", {
            "slide": slide_id,
            "dropoff_slot": dropoff_slot
        }); time.sleep(0.1)

    def move_from_idle_to_opentrons(self, slide_id: int, opentrons_slot: int):
        """Move from idle position to opentrons to pick up slide"""
        self.emit("robot.move_idle_to_opentrons", {
            "slide": slide_id,
            "opentrons_slot": opentrons_slot
        }); time.sleep(0.1)

    def move_from_idle_to_microscope(self, slide_id: int):
        """Move from idle position to microscope to pick up slide"""
        self.emit("robot.move_idle_to_microscope", {
            "slide": slide_id
        }); time.sleep(0.1)

    def move_safety(self):
        """Move to safety position"""
        self.emit("robot.safety", {}); time.sleep(0.03)