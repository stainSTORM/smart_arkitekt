"""
Enhanced visualization for the multi-device workflow.

Provides both console output and optional matplotlib-based live visualization
showing stations and active operations.
"""

from typing import Dict, Tuple, Optional
import threading
import time
import os

# Try to import matplotlib, handle gracefully if not available
try:
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    # Use non-GUI backend for headless environments
    matplotlib.use('Agg')
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    matplotlib = None
    plt = None
    patches = None

class MatplotlibVisualizer:
    """
    2D Matplotlib visualization showing stations and current action.
    Handles headless mode gracefully and provides simple station layout.
    """
    
    def __init__(self, headless: bool = None, save_frames: bool = False):
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is not available")
            
        if headless is None:
            # Auto-detect headless environment
            headless = 'DISPLAY' not in os.environ or os.environ.get('DISPLAY', '') == ''
            
        self.headless = headless
        self.save_frames = save_frames
        self.frame_count = 0
        
        # Station positions (x, y) - arbitrary layout
        self.stations = {
            'RACK': (1, 4),
            'ROBOT': (3, 3),
            'OPENTRONS': (5, 4),
            'MICROSCOPE': (5, 2),
            'DROPOFF': (1, 2)
        }
        
        self.active_station = None
        self.current_action = ""
        
        if not self.headless:
            plt.ion()  # Interactive mode
            
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self._setup_plot()
        
    def _setup_plot(self):
        """Initialize the static elements of the plot"""
        self.ax.clear()
        self.ax.set_xlim(0, 6)
        self.ax.set_ylim(1, 5)
        self.ax.set_aspect('equal')
        self.ax.set_title('Multi-Device Workflow Status')
        
        # Draw station circles and labels
        for station, (x, y) in self.stations.items():
            circle = patches.Circle((x, y), 0.3, 
                                  facecolor='lightblue', 
                                  edgecolor='black', 
                                  linewidth=1)
            self.ax.add_patch(circle)
            self.ax.text(x, y-0.6, station, ha='center', fontsize=8, weight='bold')
            
        # Add arrows showing workflow direction
        self._draw_workflow_arrows()
        
    def _draw_workflow_arrows(self):
        """Draw arrows showing the workflow direction between stations"""
        # RACK -> ROBOT
        self.ax.annotate('', xy=self.stations['ROBOT'], xytext=self.stations['RACK'],
                        arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5))
        
        # ROBOT -> OPENTRONS  
        self.ax.annotate('', xy=self.stations['OPENTRONS'], xytext=self.stations['ROBOT'],
                        arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5))
        
        # OPENTRONS -> MICROSCOPE (via ROBOT)
        self.ax.annotate('', xy=self.stations['MICROSCOPE'], xytext=self.stations['OPENTRONS'],
                        arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5))
        
        # MICROSCOPE -> DROPOFF (via ROBOT)
        self.ax.annotate('', xy=self.stations['DROPOFF'], xytext=self.stations['MICROSCOPE'],
                        arrowprops=dict(arrowstyle='->', color='gray', alpha=0.5))
        
    def _get_station_from_action(self, action_name: str) -> Optional[str]:
        """Map action names to station names"""
        if action_name.startswith('robot'):
            return 'ROBOT'
        elif action_name.startswith('opentrons'):
            return 'OPENTRONS'
        elif action_name.startswith('microscope'):
            return 'MICROSCOPE'
        elif action_name.startswith('arkitekt'):
            return None  # System-wide actions
        else:
            return None
            
    def on_step(self, name: str, payload: Dict):
        """Handle workflow step events"""
        # Console output (always enabled)
        station = (name.split('.', 1)[0] if '.' in name else name).upper()
        print(f"[{station:10}] {name:24} {payload}")
        
        # Update matplotlib visualization
        self.active_station = self._get_station_from_action(name)
        self.current_action = name
        self._update_plot()
        
    def _update_plot(self):
        """Update the matplotlib visualization with current state"""
        self._setup_plot()  # Redraw base elements
        
        # Highlight active station
        if self.active_station and self.active_station in self.stations:
            x, y = self.stations[self.active_station]
            active_circle = patches.Circle((x, y), 0.35, 
                                         facecolor='yellow', 
                                         edgecolor='red', 
                                         linewidth=3,
                                         alpha=0.8)
            self.ax.add_patch(active_circle)
            
        # Show current action
        if self.current_action:
            self.ax.text(3, 0.5, f"Current: {self.current_action}", 
                        ha='center', fontsize=10, weight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))
        
        # Update display
        if not self.headless:
            plt.draw()
            plt.pause(0.01)  # Brief pause for animation effect
            
        # Save frame if requested
        if self.save_frames:
            self.fig.savefig(f'/tmp/workflow_frame_{self.frame_count:04d}.png', 
                           dpi=100, bbox_inches='tight')
            self.frame_count += 1
            
    def close(self):
        """Clean up visualization resources"""
        if not self.headless:
            plt.ioff()
        plt.close(self.fig)

class ConsoleVisualizer:
    """Simple console-only visualizer for environments without matplotlib"""
    
    def __init__(self):
        pass
        
    def on_step(self, name: str, payload: Dict):
        station = (name.split('.', 1)[0] if '.' in name else name).upper()
        print(f"[{station:10}] {name:24} {payload}")
        
    def close(self):
        pass

def create_visualizer(use_matplotlib: bool = True, **kwargs):
    """Factory function to create appropriate visualizer"""
    if use_matplotlib and MATPLOTLIB_AVAILABLE:
        try:
            return MatplotlibVisualizer(**kwargs)
        except ImportError:
            print("Warning: matplotlib not available, falling back to console visualizer")
            return ConsoleVisualizer()
    else:
        if use_matplotlib and not MATPLOTLIB_AVAILABLE:
            print("Warning: matplotlib not available, falling back to console visualizer")
        return ConsoleVisualizer()