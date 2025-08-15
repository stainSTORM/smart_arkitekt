"""
Opentrons OT-2 device implementation for staining and washing protocols.
"""

import time
from typing import Callable, Dict

class Opentrons:
    """
    Opentrons OT-2 implementation for automated staining and washing.
    Supports multiple protocols for different antibody staining steps.
    """
    
    def __init__(self, emit: Callable[[str, Dict], None]): 
        self.emit = emit
        self.current_protocol = "NONE"

    def run_staining_protocol(self, slide_id: int, slot: int, protocol: str = None):
        """
        Run staining protocol on slide.
        
        Args:
            slide_id: ID of slide being stained
            slot: Opentrons slot number
            protocol: Protocol name (e.g. "Receptor42", "Receptor0815")
        """
        protocol_name = protocol or self.current_protocol
        self.emit("opentrons.stain", {
            "slide": slide_id, 
            "slot": slot,
            "protocol": protocol_name
        }); time.sleep(0.2)

    def run_washing_protocol(self, slide_id: int, slot: int):
        """
        Run washing protocol to clean slide.
        
        Args:
            slide_id: ID of slide being washed
            slot: Opentrons slot number
        """
        self.emit("opentrons.wash", {
            "slide": slide_id, 
            "slot": slot,
            "protocol": self.current_protocol
        }); time.sleep(0.15)
        
    def set_protocol(self, protocol: str):
        """
        Set the current protocol for staining operations.
        
        Args:
            protocol: Protocol name (e.g. "Receptor42", "Receptor0815")
        """
        self.current_protocol = protocol
        self.emit("opentrons.protocol_set", {"protocol": protocol})