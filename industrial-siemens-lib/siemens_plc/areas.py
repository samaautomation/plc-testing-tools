"""
Industrial Siemens Library - Memory Areas
=========================================

Definición de todas las áreas de memoria del PLC Siemens.
"""

from enum import Enum, auto
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


class MemoryArea(Enum):
    """Áreas de memoria del PLC Siemens."""
    
    # Áreas principales
    PE = auto()    # Process Inputs (Entradas del proceso)
    PA = auto()    # Process Outputs (Salidas del proceso)
    MK = auto()    # Merkers (Marcas)
    DB = auto()    # Data Blocks (Bloques de datos)
    TM = auto()    # Timers (Temporizadores)
    CT = auto()    # Counters (Contadores)
    
    # Áreas especiales
    SYS = auto()   # System data (Datos del sistema)
    SYS_INFO = auto()  # System information (Información del sistema)
    SYS_FLAGS = auto() # System flags (Banderas del sistema)


@dataclass
class AreaInfo:
    """Información detallada de un área de memoria."""
    name: str
    description: str
    snap7_code: int
    read_only: bool
    size_bytes: Optional[int] = None
    address_format: str = ""
    examples: List[str] = None


class Areas:
    """Clase estática con información de todas las áreas de memoria."""
    
    # Mapeo de áreas a información detallada
    AREA_INFO: Dict[MemoryArea, AreaInfo] = {
        MemoryArea.PE: AreaInfo(
            name="Process Inputs",
            description="Entradas digitales y analógicas del proceso",
            snap7_code=129,
            read_only=True,
            address_format="I[byte].[bit] o I[W][byte]",
            examples=["I0.0", "I0.1", "IB0", "IW96", "ID100"]
        ),
        
        MemoryArea.PA: AreaInfo(
            name="Process Outputs",
            description="Salidas digitales y analógicas del proceso",
            snap7_code=130,
            read_only=False,
            address_format="Q[byte].[bit] o Q[W][byte]",
            examples=["Q0.0", "Q0.1", "QB0", "QW96", "QD100"]
        ),
        
        MemoryArea.MK: AreaInfo(
            name="Merkers",
            description="Marcas internas del PLC (memoria de trabajo)",
            snap7_code=131,
            read_only=False,
            address_format="M[byte].[bit] o M[W][byte]",
            examples=["M0.0", "M0.1", "MB0", "MW10", "MD20"]
        ),
        
        MemoryArea.DB: AreaInfo(
            name="Data Blocks",
            description="Bloques de datos del PLC",
            snap7_code=132,
            read_only=False,
            address_format="DB[number].DB[W][byte]",
            examples=["DB1.DBW0", "DB2.DBD10", "DB3.DBX5.0"]
        ),
        
        MemoryArea.TM: AreaInfo(
            name="Timers",
            description="Temporizadores del PLC",
            snap7_code=29,
            read_only=False,
            address_format="T[number]",
            examples=["T1", "T2", "T10"]
        ),
        
        MemoryArea.CT: AreaInfo(
            name="Counters",
            description="Contadores del PLC",
            snap7_code=28,
            read_only=False,
            address_format="C[number]",
            examples=["C1", "C2", "C10"]
        ),
        
        MemoryArea.SYS: AreaInfo(
            name="System Data",
            description="Datos del sistema del PLC",
            snap7_code=3,
            read_only=True,
            address_format="SYS[address]",
            examples=["SYS0", "SYS1", "SYS100"]
        ),
        
        MemoryArea.SYS_INFO: AreaInfo(
            name="System Information",
            description="Información del sistema del PLC",
            snap7_code=4,
            read_only=True,
            address_format="SYS_INFO[address]",
            examples=["SYS_INFO0", "SYS_INFO1"]
        ),
        
        MemoryArea.SYS_FLAGS: AreaInfo(
            name="System Flags",
            description="Banderas del sistema del PLC",
            snap7_code=5,
            read_only=True,
            address_format="SYS_FLAGS[address]",
            examples=["SYS_FLAGS0", "SYS_FLAGS1"]
        )
    }
    
    @classmethod
    def get_info(cls, area: MemoryArea) -> AreaInfo:
        """Obtiene información detallada de un área de memoria."""
        return cls.AREA_INFO.get(area)
    
    @classmethod
    def get_snap7_code(cls, area: MemoryArea) -> int:
        """Obtiene el código Snap7 de un área de memoria."""
        info = cls.get_info(area)
        return info.snap7_code if info else 0
    
    @classmethod
    def is_read_only(cls, area: MemoryArea) -> bool:
        """Verifica si un área de memoria es de solo lectura."""
        info = cls.get_info(area)
        return info.read_only if info else True
    
    @classmethod
    def get_address_format(cls, area: MemoryArea) -> str:
        """Obtiene el formato de dirección de un área de memoria."""
        info = cls.get_info(area)
        return info.address_format if info else ""
    
    @classmethod
    def get_examples(cls, area: MemoryArea) -> List[str]:
        """Obtiene ejemplos de direcciones para un área de memoria."""
        info = cls.get_info(area)
        return info.examples if info else []
    
    @classmethod
    def get_area_by_snap7_code(cls, snap7_code: int) -> Optional[MemoryArea]:
        """Obtiene un área de memoria por su código Snap7."""
        for area, info in cls.AREA_INFO.items():
            if info.snap7_code == snap7_code:
                return area
        return None


class AddressParser:
    """Clase para parsear y validar direcciones de memoria."""
    
    @staticmethod
    def parse_address(address: str) -> Dict[str, Any]:
        """
        Parsea una dirección de memoria del PLC.
        
        Args:
            address: Dirección en formato estándar (ej: "I0.0", "DB1.DBW0")
            
        Returns:
            Diccionario con información de la dirección parseada
        """
        import re
        
        # Patrones para diferentes tipos de direcciones
        patterns = {
            # Entradas digitales: I0.0, I1.5
            r'^I(\d+)\.(\d+)$': {
                'area': MemoryArea.PE,
                'type': 'bit',
                'byte': lambda m: int(m.group(1)),
                'bit': lambda m: int(m.group(2)),
                'size': 1
            },
            
            # Salidas digitales: Q0.0, Q1.5
            r'^Q(\d+)\.(\d+)$': {
                'area': MemoryArea.PA,
                'type': 'bit',
                'byte': lambda m: int(m.group(1)),
                'bit': lambda m: int(m.group(2)),
                'size': 1
            },
            
            # Marcas: M0.0, M1.5
            r'^M(\d+)\.(\d+)$': {
                'area': MemoryArea.MK,
                'type': 'bit',
                'byte': lambda m: int(m.group(1)),
                'bit': lambda m: int(m.group(2)),
                'size': 1
            },
            
            # Entradas byte: IB0, IB1
            r'^IB(\d+)$': {
                'area': MemoryArea.PE,
                'type': 'byte',
                'byte': lambda m: int(m.group(1)),
                'size': 1
            },
            
            # Salidas byte: QB0, QB1
            r'^QB(\d+)$': {
                'area': MemoryArea.PA,
                'type': 'byte',
                'byte': lambda m: int(m.group(1)),
                'size': 1
            },
            
            # Marcas byte: MB0, MB1
            r'^MB(\d+)$': {
                'area': MemoryArea.MK,
                'type': 'byte',
                'byte': lambda m: int(m.group(1)),
                'size': 1
            },
            
            # Entradas word: IW0, IW2
            r'^IW(\d+)$': {
                'area': MemoryArea.PE,
                'type': 'word',
                'byte': lambda m: int(m.group(1)),
                'size': 2
            },
            
            # Salidas word: QW0, QW2
            r'^QW(\d+)$': {
                'area': MemoryArea.PA,
                'type': 'word',
                'byte': lambda m: int(m.group(1)),
                'size': 2
            },
            
            # Marcas word: MW0, MW2
            r'^MW(\d+)$': {
                'area': MemoryArea.MK,
                'type': 'word',
                'byte': lambda m: int(m.group(1)),
                'size': 2
            },
            
            # Entradas double word: ID0, ID4
            r'^ID(\d+)$': {
                'area': MemoryArea.PE,
                'type': 'dword',
                'byte': lambda m: int(m.group(1)),
                'size': 4
            },
            
            # Salidas double word: QD0, QD4
            r'^QD(\d+)$': {
                'area': MemoryArea.PA,
                'type': 'dword',
                'byte': lambda m: int(m.group(1)),
                'size': 4
            },
            
            # Marcas double word: MD0, MD4
            r'^MD(\d+)$': {
                'area': MemoryArea.MK,
                'type': 'dword',
                'byte': lambda m: int(m.group(1)),
                'size': 4
            },
            
            # Data blocks: DB1.DBW0, DB2.DBD10
            r'^DB(\d+)\.DB([BWD])(\d+)$': {
                'area': MemoryArea.DB,
                'type': lambda m: m.group(2).lower(),
                'db_number': lambda m: int(m.group(1)),
                'byte': lambda m: int(m.group(3)),
                'size': lambda m: {'b': 1, 'w': 2, 'd': 4}[m.group(2).lower()]
            },
            
            # Data blocks bit: DB1.DBX5.0
            r'^DB(\d+)\.DBX(\d+)\.(\d+)$': {
                'area': MemoryArea.DB,
                'type': 'bit',
                'db_number': lambda m: int(m.group(1)),
                'byte': lambda m: int(m.group(2)),
                'bit': lambda m: int(m.group(3)),
                'size': 1
            },
            
            # Temporizadores: T1, T2
            r'^T(\d+)$': {
                'area': MemoryArea.TM,
                'type': 'timer',
                'number': lambda m: int(m.group(1)),
                'size': 2
            },
            
            # Contadores: C1, C2
            r'^C(\d+)$': {
                'area': MemoryArea.CT,
                'type': 'counter',
                'number': lambda m: int(m.group(1)),
                'size': 2
            }
        }
        
        for pattern, config in patterns.items():
            match = re.match(pattern, address)
            if match:
                result = {
                    'address': address,
                    'area': config['area'],
                    'type': config['type'](match) if callable(config['type']) else config['type'],
                    'size': config['size'](match) if callable(config['size']) else config['size']
                }
                
                # Agregar campos específicos según el tipo
                for key, value in config.items():
                    if key not in ['area', 'type', 'size'] and callable(value):
                        result[key] = value(match)
                    elif key not in ['area', 'type', 'size']:
                        result[key] = value
                
                return result
        
        raise ValueError(f"Formato de dirección no válido: {address}")
    
    @staticmethod
    def validate_address(address: str) -> bool:
        """Valida si una dirección tiene el formato correcto."""
        try:
            AddressParser.parse_address(address)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_address_info(address: str) -> Dict[str, Any]:
        """Obtiene información completa de una dirección."""
        parsed = AddressParser.parse_address(address)
        area_info = Areas.get_info(parsed['area'])
        
        return {
            **parsed,
            'area_name': area_info.name if area_info else "Unknown",
            'area_description': area_info.description if area_info else "",
            'read_only': area_info.read_only if area_info else True,
            'snap7_code': area_info.snap7_code if area_info else 0
        }


class AddressBuilder:
    """Clase para construir direcciones de memoria."""
    
    @staticmethod
    def build_digital_input(byte: int, bit: int) -> str:
        """Construye una dirección de entrada digital."""
        return f"I{byte}.{bit}"
    
    @staticmethod
    def build_digital_output(byte: int, bit: int) -> str:
        """Construye una dirección de salida digital."""
        return f"Q{byte}.{bit}"
    
    @staticmethod
    def build_mark(byte: int, bit: int) -> str:
        """Construye una dirección de marca."""
        return f"M{byte}.{bit}"
    
    @staticmethod
    def build_analog_input(byte: int) -> str:
        """Construye una dirección de entrada analógica."""
        return f"IW{byte}"
    
    @staticmethod
    def build_analog_output(byte: int) -> str:
        """Construye una dirección de salida analógica."""
        return f"QW{byte}"
    
    @staticmethod
    def build_data_block(db_number: int, byte: int, data_type: str = 'W') -> str:
        """Construye una dirección de bloque de datos."""
        return f"DB{db_number}.DB{data_type.upper()}{byte}"
    
    @staticmethod
    def build_timer(number: int) -> str:
        """Construye una dirección de temporizador."""
        return f"T{number}"
    
    @staticmethod
    def build_counter(number: int) -> str:
        """Construye una dirección de contador."""
        return f"C{number}"


# Constantes útiles
DEFAULT_AREAS = {
    'inputs': MemoryArea.PE,
    'outputs': MemoryArea.PA,
    'marks': MemoryArea.MK,
    'data_blocks': MemoryArea.DB,
    'timers': MemoryArea.TM,
    'counters': MemoryArea.CT
}

# Mapeo de tipos de datos a tamaños
DATA_TYPE_SIZES = {
    'bit': 1,
    'byte': 1,
    'word': 2,
    'dword': 4,
    'timer': 2,
    'counter': 2
} 