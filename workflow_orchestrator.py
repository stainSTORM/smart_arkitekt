"""
Multi-device workflow orchestrator for Arkitekt.

Implements a state-machine that executes slide workflow across three devices:
- Robot Arm: handles slide movement between stations
- Opentrons: runs staining and washing protocols  
- Microscope: evaluates slide quality and performs full scans

Supports multiple slides, configurable wash loops, and provides hooks for
Arkitekt task integration with live visualization.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional
import time
import random

# ---------- Domain ----------
class Station(Enum):
    RACK = auto()
    ROBOT = auto() 
    OPENTRONS = auto()
    MICROSCOPE = auto()
    DROPOFF = auto()

@dataclass
class Slide:
    id: int
    loop_count: int = 0
    is_ok: Optional[bool] = None

# ---------- Devices ----------
class RobotArm:
    def __init__(self, emit: Callable[[str, Dict], None]): 
        self.emit = emit

    # Diagram aliases in comments
    def move_start_position(self):                      # moveStartpositionRobot()
        self.emit("robot.move_start", {}); time.sleep(0.05)

    def move_pickup_position(self, slot: int):          # movePickuppositionRobotarm(slot_num_Pickup)
        self.emit("robot.move_pickup", {"slot": slot}); time.sleep(0.05)

    def close_gripper(self):                            # closeRobotgripper()
        self.emit("robot.close_gripper", {}); time.sleep(0.02)

    def open_gripper(self):                             # openRobotgripper()
        self.emit("robot.open_gripper", {}); time.sleep(0.02)

    def move_to_opentrons(self, slide_id: int, slot: int, state: str = "ready"):
        # moveToOpentrons(part_id, slot_num_opentron, state_opentron)
        self.emit("robot.to_opentrons", {"slide": slide_id, "slot": slot, "state": state}); time.sleep(0.1)

    def move_to_microscope(self, slide_id: int, state: str = "ready"):
        # moveMicroscopeRobotarm(part_id, state_microscope)
        self.emit("robot.to_microscope", {"slide": slide_id, "state": state}); time.sleep(0.1)

    def move_to_dropoff(self, slide_id: int, slot: int):
        # moveDropoffstationRobotarm(part_id, slot_num_dropoff)
        self.emit("robot.to_dropoff", {"slide": slide_id, "slot": slot}); time.sleep(0.1)

    def move_safety(self):                              # movesafetyRobotarm()
        self.emit("robot.safety", {}); time.sleep(0.03)

class Opentrons:
    def __init__(self, emit: Callable[[str, Dict], None]): 
        self.emit = emit

    def run_staining_protocol(self, slide_id: int, slot: int):
        # run_staining_protocol(part_id, slot_num_opentron)
        self.emit("opentrons.stain", {"slide": slide_id, "slot": slot}); time.sleep(0.2)

    def run_washing_protocol(self, slide_id: int, slot: int):
        # run_washing_protocol()
        self.emit("opentrons.wash", {"slide": slide_id, "slot": slot}); time.sleep(0.15)

class Microscope:
    def __init__(self, emit: Callable[[str, Dict], None]): 
        self.emit = emit

    def safety(self):                                   # safetyMicroscope()
        self.emit("microscope.safety", {}); time.sleep(0.03)

    def evaluate(self, slide_id: int) -> bool:          # evaluateMicroscope(part_id) -> 1/0
        self.emit("microscope.evaluate", {"slide": slide_id})
        time.sleep(0.1)
        # Placeholder heuristic: progressively more likely to be OK after washes
        # Replace with Arkitekt-driven analysis result.
        return bool(random.random() > 0.4)

    def scan_slide(self, slide_id: int):
        self.emit("microscope.scan", {"slide": slide_id}); time.sleep(0.25)

# ---------- Visualization (minimal hooks) ----------
class Visualizer:
    """Very simple stdout tracer. Replace with Matplotlib renderer as needed."""
    def __init__(self): 
        pass
        
    def on_step(self, name: str, payload: Dict):
        station = (name.split('.', 1)[0] if '.' in name else name).upper()
        print(f"[{station:10}] {name:24} {payload}")

# ---------- Orchestrator ----------
class Orchestrator:
    def __init__(self,
                 robot: RobotArm,
                 ot: Opentrons,
                 scope: Microscope,
                 emit: Callable[[str, Dict], None],
                 max_wash_loops: int = 2,
                 pickup_slot: int = 1,
                 ot_slot: int = 1,
                 dropoff_slot: int = 1):
        self.robot = robot
        self.ot = ot
        self.scope = scope
        self.emit = emit
        self.max_wash_loops = max_wash_loops
        self.pickup_slot = pickup_slot
        self.ot_slot = ot_slot
        self.dropoff_slot = dropoff_slot

    def run(self, slide_ids: List[int]):
        self.emit("arkitekt.start", {"slides": slide_ids})

        for sid in slide_ids:
            slide = Slide(id=sid)

            # Pickup from rack
            self.robot.move_start_position()
            self.robot.move_pickup_position(self.pickup_slot)
            self.robot.close_gripper()
            self.robot.move_to_opentrons(slide.id, self.ot_slot, state="receive")
            self.robot.open_gripper()
            self.robot.move_safety()

            # Initial staining
            self.ot.run_staining_protocol(slide.id, self.ot_slot)

            # Loop: evaluate -> if not OK -> wash -> re-evaluate
            while True:
                # Pick from Opentrons to Microscope
                self.robot.move_to_opentrons(slide.id, self.ot_slot, state="pickup")
                self.robot.close_gripper()
                self.scope.safety()
                self.robot.move_to_microscope(slide.id, state="deliver")
                self.robot.open_gripper()
                self.robot.move_safety()

                # Evaluate (low-mag, few frames)
                slide.is_ok = self.scope.evaluate(slide.id)

                if slide.is_ok:
                    # Full scan + return to drop-off
                    self.scope.scan_slide(slide.id)
                    self.scope.safety()
                    self.robot.move_to_microscope(slide.id, state="pickup")
                    self.robot.close_gripper()
                    self.robot.move_to_dropoff(slide.id, self.dropoff_slot)
                    self.robot.open_gripper()
                    self.robot.move_safety()
                    self.emit("arkitekt.slide_done", {"slide": sid, "loops": slide.loop_count})
                    break

                # Not OK → wash if available
                if slide.loop_count >= self.max_wash_loops:
                    self.emit("arkitekt.failed_quality", {"slide": sid, "loops": slide.loop_count})
                    # Decide policy: drop-off anyway or send to reject bin
                    self.scope.safety()
                    self.robot.move_to_microscope(slide.id, state="pickup")
                    self.robot.close_gripper()
                    self.robot.move_to_dropoff(slide.id, self.dropoff_slot)
                    self.robot.open_gripper()
                    self.robot.move_safety()
                    break

                # Send back for washing
                self.scope.safety()
                self.robot.move_to_microscope(slide.id, state="pickup")
                self.robot.close_gripper()
                self.robot.move_to_opentrons(slide.id, self.ot_slot, state="wash")
                self.robot.open_gripper()
                self.robot.move_safety()
                self.ot.run_washing_protocol(slide.id, self.ot_slot)
                slide.loop_count += 1

        self.emit("arkitekt.done", {})

# ---------- Wiring / Demo ----------
def build_demo(max_wash_loops: int = 2) -> Orchestrator:
    viz = Visualizer()
    emit = viz.on_step
    robot = RobotArm(emit)
    ot = Opentrons(emit)
    scope = Microscope(emit)
    return Orchestrator(robot, ot, scope, emit, max_wash_loops=max_wash_loops)

if __name__ == "__main__":
    orch = build_demo(max_wash_loops=2)
    orch.run([1, 2, 3, 4])