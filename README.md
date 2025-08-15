# Multi-Device Workflow Orchestrator

A minimal, testable state-machine that executes slide workflows across three devices (Robot Arm, Opentrons, Microscope) with live visualization and Arkitekt integration hooks.

## Features

- **Multi-device coordination**: Robot Arm, Opentrons OT-2, and Microscope
- **Automated slide processing**: Pickup → Stain → Evaluate → [Wash if needed] → Scan → Drop-off
- **Quality control**: Configurable wash loops with automatic retry logic
- **Live visualization**: Console output + optional Matplotlib visualization
- **Arkitekt integration**: Event hooks ready for task delegation and result handling
- **Headless support**: Runs in CI/CD environments without display

## Quick Start

### Basic Demo
```bash
python3 demo.py --slides 1 2 3 4
```

### Console-only (no matplotlib)
```bash
python3 demo.py --no-matplotlib --slides 1 2
```

### With visualization frames saved
```bash
python3 demo.py --save-frames --headless --slides 1
```

### Test wash loops specifically
```bash
python3 test_wash_loops.py
```

## Workflow Overview

```
RACK → [Robot picks up] → OPENTRONS → [Staining] → 
MICROSCOPE → [Evaluation] → 
├─ ✅ OK → [Full scan] → DROPOFF
└─ ❌ Not OK → OPENTRONS → [Washing] → MICROSCOPE (retry up to max_wash_loops)
```

## Architecture

### Core Components

- **`workflow_orchestrator.py`**: Main orchestrator with device classes and state machine
- **`visualizer.py`**: Console and matplotlib-based visualization 
- **`demo.py`**: Command-line demo script
- **`test_wash_loops.py`**: Wash loop functionality testing

### Device APIs

#### Robot Arm
- `move_start_position()`, `move_pickup_position(slot)` 
- `close_gripper()`, `open_gripper()`
- `move_to_opentrons(slide_id, slot, state)`
- `move_to_microscope(slide_id, state)`
- `move_to_dropoff(slide_id, slot)`, `move_safety()`

#### Opentrons OT-2
- `run_staining_protocol(slide_id, slot)`
- `run_washing_protocol(slide_id, slot)`

#### Microscope  
- `safety()`, `evaluate(slide_id) -> bool`, `scan_slide(slide_id)`

### Event System

All device operations emit events through a configurable callback:
```python
emit("device.action", {"slide": slide_id, "slot": slot, ...})
```

Events include:
- `robot.*` - Robot arm movements and gripper actions
- `opentrons.*` - Staining and washing protocols  
- `microscope.*` - Safety, evaluation, and scanning
- `arkitekt.*` - Workflow start/completion and slide status

## Configuration

### Orchestrator Parameters
```python
Orchestrator(
    robot=robot,
    ot=opentrons, 
    scope=microscope,
    emit=event_callback,
    max_wash_loops=2,      # Max washing attempts per slide
    pickup_slot=1,         # Rack slot for pickup
    ot_slot=1,            # Opentrons slot
    dropoff_slot=1        # Drop-off slot
)
```

### Visualization Options
```python
# Console only
viz = create_visualizer(use_matplotlib=False)

# Matplotlib with frame saving
viz = create_visualizer(
    use_matplotlib=True,
    headless=True,         # No interactive display
    save_frames=True       # Save PNG frames to /tmp
)
```

## Arkitekt Integration

The system is designed for easy Arkitekt task integration:

### Current (Mock Implementation)
```python
def evaluate(self, slide_id: int) -> bool:
    # Placeholder random evaluation
    return bool(random.random() > 0.4)
```

### Future Arkitekt Integration
```python
def evaluate(self, slide_id: int) -> bool:
    # Submit analysis task to Arkitekt
    task = arkitekt.submit_task("slide_analysis", slide_id=slide_id)
    result = await task.result()
    return result.quality_ok
```

The orchestrator API remains unchanged - just swap device implementations.

## Testing

### Acceptance Criteria Verification

✅ **Run demo with slides [1,2,3,4]**: `python3 demo.py`
✅ **Quality evaluation with wash loops**: `python3 test_wash_loops.py`
✅ **Failed quality handling**: Slides failing max_wash_loops are dropped off
✅ **Headless visualization**: Works without display, saves frames to /tmp
✅ **Arkitekt-ready architecture**: Device methods can be swapped with async tasks

### Example Output
```
🔬 Starting Multi-Device Workflow Demo
   Slides: [1, 2, 3, 4]
   Max wash loops: 2
   Visualization: Matplotlib
==================================================
[ARKITEKT  ] arkitekt.start           {'slides': [1, 2, 3, 4]}
[ROBOT     ] robot.move_start         {}
[ROBOT     ] robot.move_pickup        {'slot': 1}
[ROBOT     ] robot.close_gripper      {}
[ROBOT     ] robot.to_opentrons       {'slide': 1, 'slot': 1, 'state': 'receive'}
...
[ARKITEKT  ] arkitekt.slide_done      {'slide': 1, 'loops': 0}
...
==================================================
✅ Workflow completed successfully!
   Total time: 2.85 seconds
   Processed 4 slides
```

## Dependencies

- **Core**: Python 3.8+ (dataclasses, enum, typing)
- **Visualization**: matplotlib (optional, graceful fallback to console)
- **No other external dependencies**

## File Structure

```
smart_arkitekt/
├── workflow_orchestrator.py    # Main orchestration logic
├── visualizer.py               # Console + matplotlib visualization  
├── demo.py                     # Command-line demo script
├── test_wash_loops.py          # Wash loop testing
└── README.md                   # This file
```