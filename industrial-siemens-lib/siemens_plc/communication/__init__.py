"""
Industrial Communication Module
==============================

Módulo de comunicación PLC-PLC y VFD.
Soporte para comunicación entre múltiples dispositivos industriales.
"""

from .plc_plc import PLCToPLCCommunication, PLCNetwork
from .vfd_communication import VFDCommunication, VFDProtocol
from .network_manager import NetworkManager
from .data_sync import DataSynchronizer
from .protocol_bridge import ProtocolBridge

__all__ = [
    # PLC-PLC Communication
    "PLCToPLCCommunication",
    "PLCNetwork",
    
    # VFD Communication
    "VFDCommunication", 
    "VFDProtocol",
    
    # Network Management
    "NetworkManager",
    
    # Data Synchronization
    "DataSynchronizer",
    
    # Protocol Bridge
    "ProtocolBridge"
] 