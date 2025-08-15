#!/usr/bin/env python3
"""
Demo script for the multi-device workflow orchestrator.

Runs the complete workflow with slides [1,2,3,4] and demonstrates:
- Multi-slide processing
- Quality evaluation with wash loops
- Live visualization
- Event emission and logging
"""

import sys
import os
import argparse
import time
from typing import List

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow_orchestrator import (
    RobotArm, Opentrons, Microscope, Orchestrator, Slide, Station
)
from visualizer import create_visualizer

def run_demo(slide_ids: List[int] = None, max_wash_loops: int = 2, 
             use_matplotlib: bool = True, save_frames: bool = False,
             headless: bool = None):
    """
    Run the complete workflow demonstration.
    
    Args:
        slide_ids: List of slide IDs to process (default: [1,2,3,4])
        max_wash_loops: Maximum number of wash attempts per slide
        use_matplotlib: Whether to use matplotlib visualization
        save_frames: Whether to save visualization frames to /tmp
        headless: Force headless mode (auto-detect if None)
    """
    if slide_ids is None:
        slide_ids = [1, 2, 3, 4]
        
    print(f"🔬 Starting Multi-Device Workflow Demo")
    print(f"   Slides: {slide_ids}")
    print(f"   Max wash loops: {max_wash_loops}")
    print(f"   Visualization: {'Matplotlib' if use_matplotlib else 'Console'}")
    print("=" * 50)
    
    # Create visualizer
    viz = create_visualizer(
        use_matplotlib=use_matplotlib, 
        headless=headless,
        save_frames=save_frames
    )
    
    try:
        # Create devices with event emission
        emit = viz.on_step
        robot = RobotArm(emit)
        ot = Opentrons(emit)
        scope = Microscope(emit)
        
        # Create orchestrator
        orchestrator = Orchestrator(
            robot=robot,
            ot=ot, 
            scope=scope,
            emit=emit,
            max_wash_loops=max_wash_loops
        )
        
        # Run the workflow
        start_time = time.time()
        orchestrator.run(slide_ids)
        end_time = time.time()
        
        print("=" * 50)
        print(f"✅ Workflow completed successfully!")
        print(f"   Total time: {end_time - start_time:.2f} seconds")
        print(f"   Processed {len(slide_ids)} slides")
        
        if save_frames:
            print(f"   Visualization frames saved to /tmp/workflow_frame_*.png")
            
    except KeyboardInterrupt:
        print("\n⚠️  Workflow interrupted by user")
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        raise
    finally:
        # Clean up visualization
        viz.close()

def main():
    """Main entry point with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description='Run the multi-device workflow demonstration'
    )
    
    parser.add_argument(
        '--slides', 
        type=int, 
        nargs='+', 
        default=[1, 2, 3, 4],
        help='Slide IDs to process (default: 1 2 3 4)'
    )
    
    parser.add_argument(
        '--max-wash-loops',
        type=int,
        default=2,
        help='Maximum wash loops per slide (default: 2)'
    )
    
    parser.add_argument(
        '--no-matplotlib',
        action='store_true',
        help='Disable matplotlib visualization (console only)'
    )
    
    parser.add_argument(
        '--save-frames',
        action='store_true', 
        help='Save visualization frames to /tmp'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Force headless mode (no interactive display)'
    )
    
    args = parser.parse_args()
    
    run_demo(
        slide_ids=args.slides,
        max_wash_loops=args.max_wash_loops,
        use_matplotlib=not args.no_matplotlib,
        save_frames=args.save_frames,
        headless=args.headless
    )

if __name__ == "__main__":
    main()