#!/usr/bin/env python3
"""
Test script for Siemens PLC library - Using available methods
"""

import sys
import os

# Add parent directory to path
sys.path.append('..')

print("🚀 PRUEBA PLC SIEMENS - MÉTODOS DISPONIBLES")
print("=" * 50)

try:
    print("📦 Importando librería...")
    from siemens_plc.connection import SiemensPLC
    from snap7 import Area
    print("✅ Librería importada correctamente")
    
    # Test connection
    print("\n🔌 Probando conexión al PLC...")
    print("IP: 192.168.1.5")
    print("Rack: 0, Slot: 1")
    
    plc = SiemensPLC(
        ip="192.168.1.5",
        rack=0,
        slot=1,
        debug=True  # Enable debug output
    )
    
    # Connect
    print("\n🔄 Conectando...")
    plc.connect()
    print("✅ ¡CONEXIÓN EXITOSA!")
    
    # Get connection info
    print("\n📊 Información de conexión:")
    info = plc.get_connection_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Get CPU info
    print("\n🖥️ Información del CPU:")
    try:
        cpu_info = plc.get_cpu_info()
        for key, value in cpu_info.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ Error obteniendo info del CPU: {e}")
    
    # Get order code
    print("\n🏷️ Código de orden:")
    try:
        order_code = plc.get_order_code()
        print(f"  Código: {order_code}")
    except Exception as e:
        print(f"❌ Error obteniendo código de orden: {e}")
    
    # Test reading digital inputs (E area)
    print("\n📖 Probando lectura de entradas digitales (E0.0)...")
    try:
        # Read 1 byte from E area (digital inputs)
        # E0.0 is the first bit of the first byte
        data = plc.read_area(Area.PE, 0, 0, 1)  # PE = Process Inputs
        print(f"✅ Datos leídos: {data.hex()}")
        
        # Extract bit 0 (E0.0)
        bit_value = bool(data[0] & 0x01)
        print(f"✅ E0.0 = {bit_value} ({'ON' if bit_value else 'OFF'})")
        
    except Exception as e:
        print(f"❌ Error leyendo entradas: {e}")
    
    # Test writing digital outputs (A area)
    print("\n✍️ Probando escritura de salidas digitales (A0.0)...")
    try:
        # Read current state
        current_data = plc.read_area(Area.PA, 0, 0, 1)  # PA = Process Outputs
        print(f"  Estado actual: {current_data.hex()}")
        
        # Set bit 0 (A0.0) to ON
        new_data = bytearray(current_data)
        new_data[0] |= 0x01  # Set bit 0
        plc.write_area(Area.PA, 0, 0, bytes(new_data))
        print("✅ A0.0 = ON")
        
        # Read back to verify
        verify_data = plc.read_area(Area.PA, 0, 0, 1)
        bit_value = bool(verify_data[0] & 0x01)
        print(f"✅ A0.0 verificado = {bit_value}")
        
        # Set bit 0 (A0.0) to OFF
        new_data[0] &= ~0x01  # Clear bit 0
        plc.write_area(Area.PA, 0, 0, bytes(new_data))
        print("✅ A0.0 = OFF")
        
    except Exception as e:
        print(f"❌ Error escribiendo salidas: {e}")
    
    # Disconnect
    print("\n🔌 Desconectando...")
    plc.disconnect()
    print("✅ Conexión cerrada")
    
    print("\n🎉 ¡PRUEBA COMPLETADA EXITOSAMENTE!")
    
except ImportError as e:
    print(f"❌ Error importando: {e}")
    print("\nVerificando archivos:")
    if os.path.exists("../siemens_plc"):
        print("✅ Directorio siemens_plc existe")
        print("Archivos en siemens_plc:")
        os.system("ls -la ../siemens_plc/")
    else:
        print("❌ Directorio siemens_plc no existe")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Tipo de error: {type(e)}") 