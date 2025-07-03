"""
Industrial Siemens Library - Protocols
======================================

Módulo de protocolos de comunicación industrial.
Soporte para Modbus, Profibus, Ethernet/IP y otros protocolos estándar.
"""

from .modbus import ModbusProtocol, ModbusTCP, ModbusRTU
from .profibus import ProfibusProtocol, ProfibusDP
from .ethernet_ip import EthernetIPProtocol
from .opc_ua import OPCUAProtocol
from .s7 import S7Protocol
from .base import BaseProtocol, ProtocolType

__all__ = [
    # Base
    "BaseProtocol",
    "ProtocolType",
    
    # Modbus
    "ModbusProtocol",
    "ModbusTCP",
    "ModbusRTU",
    
    # Profibus
    "ProfibusProtocol",
    "ProfibusDP",
    
    # Ethernet/IP
    "EthernetIPProtocol",
    
    # OPC UA
    "OPCUAProtocol",
    
    # S7
    "S7Protocol"
] 