#!/usr/bin/env python3
"""
Test script to verify wash loop functionality.

This script temporarily modifies the microscope evaluation to demonstrate
wash loops with a more predictable outcome.
"""

import random
from smart_arkitekt.microscope import Microscope

class TestMicroscope(Microscope):
    """Test microscope with predictable evaluation results for testing wash loops"""
    
    def __init__(self, emit, fail_first_n_evaluations: int = 2):
        super().__init__(emit)
        self.evaluation_count = 0
        self.fail_first_n_evaluations = fail_first_n_evaluations

    def evaluate(self, slide_id: int) -> bool:
        self.emit("microscope.evaluate", {"slide": slide_id})
        import time; time.sleep(0.1)
        
        self.evaluation_count += 1
        # Fail first N evaluations to force wash loops, then succeed
        result = self.evaluation_count > self.fail_first_n_evaluations
        
        print(f"    📊 Evaluation #{self.evaluation_count} for slide {slide_id}: {'✅ OK' if result else '❌ NOT OK'}")
        return result

def test_wash_loops():
    """Test the wash loop functionality"""
    print("🧪 Testing Wash Loop Functionality")
    print("   Will force first 2 evaluations to fail, then succeed")
    print("=" * 60)
    
    # Import here to avoid circular imports
    from smart_arkitekt.visualizer import create_visualizer
    from smart_arkitekt.orchestrator import Orchestrator
    from smart_arkitekt.robot_arm import RobotArm
    from smart_arkitekt.opentrons import Opentrons
    from smart_arkitekt.image_processor import ImageProcessor
    
    # Create visualizer (console only for testing)
    viz = create_visualizer(use_matplotlib=False)
    
    try:
        # Create devices with test microscope
        emit = viz.on_step
        robot = RobotArm(emit)
        opentrons = Opentrons(emit)
        scope = TestMicroscope(emit, fail_first_n_evaluations=2)
        image_processor = ImageProcessor(emit)
        
        # Create orchestrator with max 3 wash loops
        orchestrator = Orchestrator(
            robot=robot,
            opentrons=opentrons, 
            microscope=scope,
            image_processor=image_processor,
            emit=emit,
            max_wash_loops=3,
            protocols=["TestProtocol"]  # Single protocol for testing
        )
        
        # Run the workflow with single slide
        import time
        start_time = time.time()
        orchestrator.run([1])
        end_time = time.time()
        
        print("=" * 60)
        print(f"✅ Wash loop test completed!")
        print(f"   Total time: {end_time - start_time:.2f} seconds")
        print(f"   Expected: 1 slide with 2 wash loops before success")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        viz.close()

if __name__ == "__main__":
    test_wash_loops()