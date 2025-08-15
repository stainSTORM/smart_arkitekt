#!/usr/bin/env python3
"""
Test script to verify wash loop functionality.

This script temporarily modifies the microscope evaluation to demonstrate
wash loops with a more predictable outcome.
"""

import sys
import os
import random

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow_orchestrator import RobotArm, Opentrons, Orchestrator
from visualizer import create_visualizer

class TestMicroscope:
    """Test microscope with predictable evaluation results for testing wash loops"""
    
    def __init__(self, emit, fail_first_n_evaluations: int = 2):
        self.emit = emit
        self.evaluation_count = 0
        self.fail_first_n_evaluations = fail_first_n_evaluations

    def safety(self):
        self.emit("microscope.safety", {}); 
        import time; time.sleep(0.03)

    def evaluate(self, slide_id: int) -> bool:
        self.emit("microscope.evaluate", {"slide": slide_id})
        import time; time.sleep(0.1)
        
        self.evaluation_count += 1
        # Fail first N evaluations to force wash loops, then succeed
        result = self.evaluation_count > self.fail_first_n_evaluations
        
        print(f"    📊 Evaluation #{self.evaluation_count} for slide {slide_id}: {'✅ OK' if result else '❌ NOT OK'}")
        return result

    def scan_slide(self, slide_id: int):
        self.emit("microscope.scan", {"slide": slide_id}); 
        import time; time.sleep(0.25)

def test_wash_loops():
    """Test the wash loop functionality"""
    print("🧪 Testing Wash Loop Functionality")
    print("   Will force first 2 evaluations to fail, then succeed")
    print("=" * 60)
    
    # Create visualizer (console only for testing)
    viz = create_visualizer(use_matplotlib=False)
    
    try:
        # Create devices with test microscope
        emit = viz.on_step
        robot = RobotArm(emit)
        ot = Opentrons(emit)
        scope = TestMicroscope(emit, fail_first_n_evaluations=2)
        
        # Create orchestrator with max 3 wash loops
        orchestrator = Orchestrator(
            robot=robot,
            ot=ot, 
            scope=scope,
            emit=emit,
            max_wash_loops=3
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