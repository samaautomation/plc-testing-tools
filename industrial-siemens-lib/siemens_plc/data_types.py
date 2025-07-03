"""
Industrial Siemens Library - Data Types
=======================================

Definición de todos los tipos de datos industriales soportados.
"""

from enum import Enum, auto
from typing import Any, Union, Optional, Dict, List
from dataclasses import dataclass
import struct


class DataType(Enum):
    """Tipos de datos industriales soportados."""
    
    # Tipos digitales
    BOOL = auto()      # 1 bit
    BYTE = auto()      # 8 bits
    WORD = auto()      # 16 bits
    DWORD = auto()     # 32 bits
    LWORD = auto()     # 64 bits
    
    # Tipos analógicos
    INT = auto()       # 16 bits signed
    UINT = auto()      # 16 bits unsigned
    DINT = auto()      # 32 bits signed
    UDINT = auto()     # 32 bits unsigned
    LINT = auto()      # 64 bits signed
    ULINT = auto()     # 64 bits unsigned
    
    # Tipos de punto flotante
    REAL = auto()      # 32 bits float
    LREAL = auto()     # 64 bits double
    
    # Tipos de tiempo
    TIME = auto()      # Tiempo en milisegundos
    TIME_OF_DAY = auto()  # Hora del día
    DATE = auto()      # Fecha
    DATE_AND_TIME = auto()  # Fecha y hora
    
    # Tipos de caracteres
    CHAR = auto()      # 8 bits character
    STRING = auto()    # String variable length
    
    # Tipos especiales
    ARRAY = auto()     # Array de elementos
    STRUCT = auto()    # Estructura personalizada
    POINTER = auto()   # Puntero
    
    # Tipos de control
    TIMER = auto()     # Temporizador
    COUNTER = auto()   # Contador


@dataclass
class DataTypeInfo:
    """Información detallada de un tipo de datos."""
    name: str
    size_bytes: int
    size_bits: int
    signed: bool
    min_value: Optional[Union[int, float]]
    max_value: Optional[Union[int, float]]
    description: str
    snap7_code: Optional[int] = None


class DataTypes:
    """Clase estática con información de todos los tipos de datos."""
    
    # Mapeo de tipos de datos a información detallada
    TYPE_INFO: Dict[DataType, DataTypeInfo] = {
        DataType.BOOL: DataTypeInfo(
            name="BOOL",
            size_bytes=1,
            size_bits=1,
            signed=False,
            min_value=0,
            max_value=1,
            description="Valor booleano (True/False)",
            snap7_code=1
        ),
        
        DataType.BYTE: DataTypeInfo(
            name="BYTE",
            size_bytes=1,
            size_bits=8,
            signed=False,
            min_value=0,
            max_value=255,
            description="Byte sin signo (8 bits)",
            snap7_code=2
        ),
        
        DataType.WORD: DataTypeInfo(
            name="WORD",
            size_bytes=2,
            size_bits=16,
            signed=False,
            min_value=0,
            max_value=65535,
            description="Palabra sin signo (16 bits)",
            snap7_code=3
        ),
        
        DataType.DWORD: DataTypeInfo(
            name="DWORD",
            size_bytes=4,
            size_bits=32,
            signed=False,
            min_value=0,
            max_value=4294967295,
            description="Doble palabra sin signo (32 bits)",
            snap7_code=4
        ),
        
        DataType.INT: DataTypeInfo(
            name="INT",
            size_bytes=2,
            size_bits=16,
            signed=True,
            min_value=-32768,
            max_value=32767,
            description="Entero con signo (16 bits)",
            snap7_code=5
        ),
        
        DataType.UINT: DataTypeInfo(
            name="UINT",
            size_bytes=2,
            size_bits=16,
            signed=False,
            min_value=0,
            max_value=65535,
            description="Entero sin signo (16 bits)",
            snap7_code=6
        ),
        
        DataType.DINT: DataTypeInfo(
            name="DINT",
            size_bytes=4,
            size_bits=32,
            signed=True,
            min_value=-2147483648,
            max_value=2147483647,
            description="Entero doble con signo (32 bits)",
            snap7_code=7
        ),
        
        DataType.REAL: DataTypeInfo(
            name="REAL",
            size_bytes=4,
            size_bits=32,
            signed=True,
            min_value=-3.402823e+38,
            max_value=3.402823e+38,
            description="Número de punto flotante (32 bits)",
            snap7_code=8
        ),
        
        DataType.LREAL: DataTypeInfo(
            name="LREAL",
            size_bytes=8,
            size_bits=64,
            signed=True,
            min_value=-1.797693e+308,
            max_value=1.797693e+308,
            description="Número de punto flotante doble (64 bits)",
            snap7_code=9
        ),
        
        DataType.TIME: DataTypeInfo(
            name="TIME",
            size_bytes=4,
            size_bits=32,
            signed=True,
            min_value=-2147483648,
            max_value=2147483647,
            description="Tiempo en milisegundos",
            snap7_code=10
        ),
        
        DataType.STRING: DataTypeInfo(
            name="STRING",
            size_bytes=0,  # Variable
            size_bits=0,   # Variable
            signed=False,
            min_value=None,
            max_value=None,
            description="Cadena de caracteres",
            snap7_code=11
        )
    }
    
    @classmethod
    def get_info(cls, data_type: DataType) -> DataTypeInfo:
        """Obtiene información detallada de un tipo de datos."""
        return cls.TYPE_INFO.get(data_type)
    
    @classmethod
    def get_size_bytes(cls, data_type: DataType) -> int:
        """Obtiene el tamaño en bytes de un tipo de datos."""
        info = cls.get_info(data_type)
        return info.size_bytes if info else 0
    
    @classmethod
    def get_size_bits(cls, data_type: DataType) -> int:
        """Obtiene el tamaño en bits de un tipo de datos."""
        info = cls.get_info(data_type)
        return info.size_bits if info else 0
    
    @classmethod
    def is_signed(cls, data_type: DataType) -> bool:
        """Verifica si un tipo de datos es con signo."""
        info = cls.get_info(data_type)
        return info.signed if info else False
    
    @classmethod
    def get_range(cls, data_type: DataType) -> tuple[Optional[Union[int, float]], Optional[Union[int, float]]]:
        """Obtiene el rango de valores de un tipo de datos."""
        info = cls.get_info(data_type)
        if info:
            return info.min_value, info.max_value
        return None, None
    
    @classmethod
    def validate_value(cls, data_type: DataType, value: Any) -> bool:
        """Valida si un valor es válido para un tipo de datos."""
        info = cls.get_info(data_type)
        if not info:
            return False
        
        if data_type == DataType.BOOL:
            return isinstance(value, bool)
        
        if data_type in [DataType.INT, DataType.UINT, DataType.DINT, DataType.UDINT]:
            if not isinstance(value, (int, float)):
                return False
            if info.min_value is not None and value < info.min_value:
                return False
            if info.max_value is not None and value > info.max_value:
                return False
            return True
        
        if data_type in [DataType.REAL, DataType.LREAL]:
            return isinstance(value, (int, float))
        
        if data_type == DataType.STRING:
            return isinstance(value, str)
        
        return True


class DataConverter:
    """Clase para conversión de tipos de datos industriales."""
    
    @staticmethod
    def bool_to_bytes(value: bool) -> bytes:
        """Convierte un valor booleano a bytes."""
        return bytes([1 if value else 0])
    
    @staticmethod
    def bytes_to_bool(data: bytes) -> bool:
        """Convierte bytes a valor booleano."""
        return bool(data[0]) if data else False
    
    @staticmethod
    def int_to_bytes(value: int, data_type: DataType) -> bytes:
        """Convierte un entero a bytes según el tipo de datos."""
        if data_type == DataType.BYTE:
            return bytes([value & 0xFF])
        elif data_type == DataType.WORD:
            return struct.pack('>H', value)
        elif data_type == DataType.DWORD:
            return struct.pack('>I', value)
        elif data_type == DataType.INT:
            return struct.pack('>h', value)
        elif data_type == DataType.DINT:
            return struct.pack('>i', value)
        else:
            raise ValueError(f"Tipo de datos no soportado para conversión: {data_type}")
    
    @staticmethod
    def bytes_to_int(data: bytes, data_type: DataType) -> int:
        """Convierte bytes a entero según el tipo de datos."""
        if data_type == DataType.BYTE:
            return data[0] if data else 0
        elif data_type == DataType.WORD:
            return struct.unpack('>H', data[:2])[0] if len(data) >= 2 else 0
        elif data_type == DataType.DWORD:
            return struct.unpack('>I', data[:4])[0] if len(data) >= 4 else 0
        elif data_type == DataType.INT:
            return struct.unpack('>h', data[:2])[0] if len(data) >= 2 else 0
        elif data_type == DataType.DINT:
            return struct.unpack('>i', data[:4])[0] if len(data) >= 4 else 0
        else:
            raise ValueError(f"Tipo de datos no soportado para conversión: {data_type}")
    
    @staticmethod
    def real_to_bytes(value: float) -> bytes:
        """Convierte un valor real a bytes."""
        return struct.pack('>f', value)
    
    @staticmethod
    def bytes_to_real(data: bytes) -> float:
        """Convierte bytes a valor real."""
        return struct.unpack('>f', data[:4])[0] if len(data) >= 4 else 0.0
    
    @staticmethod
    def lreal_to_bytes(value: float) -> bytes:
        """Convierte un valor LREAL a bytes."""
        return struct.pack('>d', value)
    
    @staticmethod
    def bytes_to_lreal(data: bytes) -> float:
        """Convierte bytes a valor LREAL."""
        return struct.unpack('>d', data[:8])[0] if len(data) >= 8 else 0.0
    
    @staticmethod
    def string_to_bytes(value: str, max_length: int = 255) -> bytes:
        """Convierte una cadena a bytes."""
        if len(value) > max_length:
            value = value[:max_length]
        return struct.pack(f'B{len(value)}s', len(value), value.encode('utf-8'))
    
    @staticmethod
    def bytes_to_string(data: bytes) -> str:
        """Convierte bytes a cadena."""
        if len(data) < 1:
            return ""
        length = data[0]
        if len(data) < length + 1:
            return ""
        return data[1:length+1].decode('utf-8', errors='ignore')
    
    @staticmethod
    def time_to_bytes(value_ms: int) -> bytes:
        """Convierte tiempo en milisegundos a bytes."""
        return struct.pack('>i', value_ms)
    
    @staticmethod
    def bytes_to_time(data: bytes) -> int:
        """Convierte bytes a tiempo en milisegundos."""
        return struct.unpack('>i', data[:4])[0] if len(data) >= 4 else 0


class DataValidator:
    """Clase para validación de tipos de datos industriales."""
    
    @staticmethod
    def validate_address(address: str) -> bool:
        """Valida una dirección de memoria del PLC."""
        import re
        # Patrones para diferentes tipos de direcciones
        patterns = [
            r'^[IQM][0-9]+\.[0-7]$',  # I0.0, Q1.5, M2.3
            r'^[IQM][BW][0-9]+$',     # IB0, QW1, MB2
            r'^DB[0-9]+\.DB[BW][0-9]+$',  # DB1.DBW0
            r'^T[0-9]+$',             # T1, T2
            r'^C[0-9]+$',             # C1, C2
        ]
        
        for pattern in patterns:
            if re.match(pattern, address):
                return True
        return False
    
    @staticmethod
    def validate_data_type(data_type: DataType) -> bool:
        """Valida si un tipo de datos es soportado."""
        return data_type in DataTypes.TYPE_INFO
    
    @staticmethod
    def validate_value_range(value: Union[int, float], data_type: DataType) -> bool:
        """Valida si un valor está en el rango permitido para el tipo de datos."""
        return DataTypes.validate_value(data_type, value)
    
    @staticmethod
    def validate_string_length(value: str, max_length: int = 255) -> bool:
        """Valida la longitud de una cadena."""
        return len(value) <= max_length


# Constantes útiles
BYTE_ORDER_BIG_ENDIAN = '>'
BYTE_ORDER_LITTLE_ENDIAN = '<'

# Mapeo de tipos de datos comunes
COMMON_DATA_TYPES = {
    'bool': DataType.BOOL,
    'byte': DataType.BYTE,
    'word': DataType.WORD,
    'dword': DataType.DWORD,
    'int': DataType.INT,
    'uint': DataType.UINT,
    'dint': DataType.DINT,
    'real': DataType.REAL,
    'lreal': DataType.LREAL,
    'time': DataType.TIME,
    'string': DataType.STRING
} 