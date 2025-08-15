#!/usr/bin/env python3
"""
Demo script for the multi-device workflow orchestrator.

Runs the complete workflow with slides [1,2,3,4] and demonstrates:
- Multi-device coordination (Robot, Opentrons, Microscope, Image Processor)
- Protocol-based staining workflow
- Quality evaluation with wash loops  
- Live visualization with active station display
- Event emission and logging
"""

import argparse
import time
from typing import List
from smart_arkitekt import build_demo

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
        
    print(f"🔬 Multi-Device Workflow Demo")
    print(f"   Slides: {slide_ids}")
    print(f"   Max wash loops: {max_wash_loops}")
    print(f"   Visualization: {'Matplotlib' if use_matplotlib else 'Console'}")
    print("=" * 50)
    
    try:
        # Create orchestrator with visualization
        orchestrator = build_demo(
            max_wash_loops=max_wash_loops,
            use_matplotlib=use_matplotlib, 
            headless=headless,
            save_frames=save_frames
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
            frame_count = getattr(orchestrator._visualizer, 'frame_count', 0)
            print(f"   Generated {frame_count} visualization frames in /tmp/")
            
    except KeyboardInterrupt:
        print("\n⚠️  Workflow interrupted by user")
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        raise
    finally:
        # Clean up visualization
        if hasattr(orchestrator, '_visualizer'):
            orchestrator._visualizer.close()

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