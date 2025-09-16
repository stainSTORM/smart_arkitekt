"""
Multi-device workflow orchestrator for Arkitekt.

Implements a state-machine that executes slide workflow across multiple devices:
- Robot Arm: handles slide movement between stations
- Opentrons: runs staining and washing protocols  
- Microscope: evaluates slide quality and performs full scans
- Image Processor: analyzes antibodies and detects cancer

Supports protocol-based workflows, configurable wash loops, and provides hooks for
Arkitekt task integration with live visualization.
"""

from typing import Callable, Dict, List, Optional
import time

from .models import Slide, Station
from .robot_arm import RobotArm
from .opentrons import Opentrons
from .microscope import Microscope
from .image_processor import ImageProcessor
from .visualizer import ConsoleVisualizer

class Orchestrator:
    """
    Main orchestrator for multi-device workflows.
    
    Coordinates all devices to execute a complete slide processing workflow
    with protocol-based staining (all slides get protocol 1, then all get protocol 2, etc).
    """
    
    def __init__(self,
                 robot: RobotArm,
                 opentrons: Opentrons,
                 microscope: Microscope,
                 image_processor: ImageProcessor,
                 emit: Callable[[str, Dict], None],
                 max_wash_loops: int = 2,
                 pickup_slot: int = 1,
                 ot_slot: int = 1,
                 dropoff_slot: int = 1, 
                 protocols: List[str] = None):
        
        self.robot = robot
        self.opentrons = opentrons
        self.microscope = microscope
        self.image_processor = image_processor
        self.emit = emit
        self.max_wash_loops = max_wash_loops
        self.pickup_slot = pickup_slot
        self.ot_slot = ot_slot
        self.dropoff_slot = dropoff_slot
        self.protocols = protocols or ["Receptor42", "Receptor0815"]

    def run(self, slide_ids: List[int]):
        """
        Execute complete multi-protocol workflow for all slides.
        
        Protocol-based workflow: all slides are processed with protocol 1,
        then all slides are processed with protocol 2, etc.
        
        Args:
            slide_ids: List of slide IDs to process
        """
        self.emit("arkitekt.workflow_start", {
            "slides": slide_ids,
            "protocols": self.protocols
        })

        # Protocol-based workflow: process all slides with each protocol in sequence
        for protocol_index, protocol in enumerate(self.protocols):
            self.emit("arkitekt.protocol_start", {
                "protocol": protocol,
                "protocol_index": protocol_index,
                "total_protocols": len(self.protocols)
            })
            
            # Set the protocol on Opentrons
            self.opentrons.set_protocol(protocol)
            
            # Process all slides with this protocol
            for slide_id in slide_ids:
                self._process_slide_with_protocol(slide_id, protocol, protocol_index == len(self.protocols) - 1)
            
            self.emit("arkitekt.protocol_complete", {"protocol": protocol})

        self.emit("arkitekt.workflow_complete", {})

    def _process_slide_with_protocol(self, slide_id: int, protocol: str, is_final_protocol: bool):
        """
        Process a single slide with the specified protocol.
        
        Args:
            slide_id: ID of slide to process
            protocol: Protocol name to use
            is_final_protocol: True if this is the last protocol in the sequence
        """
        slide = Slide(id=slide_id)
        
        self.emit("arkitekt.slide_protocol_start", {
            "slide": slide_id,
            "protocol": protocol,
            "is_final": is_final_protocol
        })

        # Step 1: Pickup from rack and move to Opentrons
        self._pickup_slide_to_opentrons(slide)
        
        # Step 2: Run staining protocol
        self.opentrons.run_staining_protocol(slide.id, self.ot_slot, protocol)
        
        # Step 3: Quality evaluation loop (only for final protocol)
        if is_final_protocol:
            self._quality_evaluation_loop(slide)
        else:
            # For intermediate protocols, just move slide back to rack for next protocol
            self._return_slide_to_rack(slide)

    def _pickup_slide_to_opentrons(self, slide: Slide):
        """Move slide from rack to Opentrons for staining"""
        self.robot.move_start_position()
        self.robot.move_pickup_position(self.pickup_slot)
        self.robot.close_gripper()
        self.robot.move_from_rack_to_opentrons(slide.id, self.ot_slot)
        self.robot.open_gripper()
        self.robot.move_safety()

    def _return_slide_to_rack(self, slide: Slide):
        """Return slide to rack after intermediate protocol (not final)"""
        self.robot.move_from_idle_to_opentrons(slide.id, self.ot_slot)
        self.robot.close_gripper()
        # For simplicity, we'll put it back in the same rack position
        # In reality, you might have separate positions for different protocol stages
        self.robot.move_start_position()  # This represents moving back to rack
        self.robot.open_gripper()
        self.robot.move_safety()

    def _quality_evaluation_loop(self, slide: Slide):
        """
        Quality evaluation loop with washing retry logic.
        Only performed after the final staining protocol.
        """
        while True:
            # Move slide from Opentrons to Microscope for evaluation
            self.robot.move_from_idle_to_opentrons(slide.id, self.ot_slot)
            self.robot.close_gripper()
            self.microscope.safety()
            self.robot.move_from_opentrons_to_microscope(slide.id, self.ot_slot)
            self.robot.open_gripper()
            self.robot.move_safety()

            # Evaluate slide quality
            slide.is_ok = self.microscope.evaluate(slide.id)

            if slide.is_ok:
                # Quality is good - proceed with full processing
                self._complete_slide_processing(slide)
                break

            # Quality not acceptable - check if we can wash
            if slide.loop_count >= self.max_wash_loops:
                # Max washes exceeded - slide failed
                self._handle_failed_slide(slide)
                break

            # Send back for washing
            self._wash_slide(slide)

    def _complete_slide_processing(self, slide: Slide):
        """Complete successful slide processing: scan -> image analysis -> dropoff"""
        # Full scan
        self.microscope.scan_slide(slide.id)
        
        # Move to image processor
        self.microscope.safety()
        self.robot.move_from_idle_to_microscope(slide.id)
        self.robot.close_gripper()
        self.robot.move_from_microscope_to_image_processor(slide.id)
        self.robot.open_gripper()
        self.robot.move_safety()
        
        # Perform image analysis
        analysis_report = self.image_processor.process_slide(slide.id)
        
        # Move to dropoff
        self.robot.close_gripper()
        self.robot.move_from_image_processor_to_dropoff(slide.id, self.dropoff_slot)
        self.robot.open_gripper()
        self.robot.move_safety()
        
        self.emit("arkitekt.slide_complete", {
            "slide": slide.id, 
            "loops": slide.loop_count,
            "analysis": analysis_report
        })

    def _handle_failed_slide(self, slide: Slide):
        """Handle slide that failed quality evaluation after max wash attempts"""
        self.emit("arkitekt.slide_failed", {
            "slide": slide.id, 
            "loops": slide.loop_count,
            "reason": "max_wash_loops_exceeded"
        })
        
        # Move directly to dropoff (or could be moved to reject bin)
        self.microscope.safety()
        self.robot.move_from_idle_to_microscope(slide.id)
        self.robot.close_gripper()
        self.robot.move_from_microscope_to_dropoff(slide.id, self.dropoff_slot)
        self.robot.open_gripper()
        self.robot.move_safety()

    def _wash_slide(self, slide: Slide):
        """Send slide back to Opentrons for washing"""
        self.microscope.safety()
        self.robot.move_from_idle_to_microscope(slide.id)
        self.robot.close_gripper()
        self.robot.move_from_microscope_to_opentrons(slide.id, self.ot_slot)
        self.robot.open_gripper()
        self.robot.move_safety()
        
        # Perform washing
        self.opentrons.run_washing_protocol(slide.id, self.ot_slot)
        slide.loop_count += 1

def build_demo(max_wash_loops: int = 2, use_matplotlib: bool = True, **viz_kwargs) -> Orchestrator:
    """
    Build a demo orchestrator with all devices and visualization.
    
    Args:
        max_wash_loops: Maximum number of wash attempts per slide
        use_matplotlib: Whether to use matplotlib visualization
        **viz_kwargs: Additional arguments for visualizer
        
    Returns:
        Configured Orchestrator instance
    """
    # Import here to avoid circular imports
    from .visualizer import create_visualizer
    
    # Create visualizer
    viz = create_visualizer(use_matplotlib=use_matplotlib, **viz_kwargs)
    emit = viz.on_step
    
    # Create devices
    robot = RobotArm(emit)
    opentrons = Opentrons(emit)
    microscope = Microscope(emit)
    image_processor = ImageProcessor(emit)
    
    # Define protocols for multi-step staining
    protocols = ["Receptor42", "Receptor0815"]
    
    # Create orchestrator
    orchestrator = Orchestrator(
        robot=robot,
        opentrons=opentrons, 
        microscope=microscope,
        image_processor=image_processor,
        emit=emit,
        max_wash_loops=max_wash_loops,
        protocols=protocols
    )
    
    # Store visualizer reference for cleanup
    orchestrator._visualizer = viz
    
    return orchestrator