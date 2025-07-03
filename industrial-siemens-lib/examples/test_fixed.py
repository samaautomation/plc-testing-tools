#!/usr/bin/env python3
"""
Test script for Siemens PLC library - Fixed version
"""

import sys
import os

# Add parent directory to path
sys.path.append('..')

print("🚀 PRUEBA BÁSICA PLC SIEMENS - VERSIÓN CORREGIDA")
print("=" * 50)

try:
    print("📦 Importando librería...")
    from siemens_plc.connection import SiemensPLCConnection
    print("✅ Librería importada correctamente")
    
    # Test connection
    print("\n🔌 Probando conexión al PLC...")
    print("IP: 192.168.1.5")
    print("Rack: 0, Slot: 1")
    
    plc = SiemensPLCConnection(
        ip_address="192.168.1.5",
        rack=0,
        slot=1
    )
    
    # Connect
    print("\n🔄 Conectando...")
    plc.connect()
    print("✅ ¡CONEXIÓN EXITOSA!")
    
    # Test reading digital input
    print("\n📖 Probando lectura E0.0...")
    try:
        value = plc.read_bit("E0.0")
        print(f"✅ E0.0 = {value} ({'ON' if value else 'OFF'})")
    except Exception as e:
        print(f"❌ Error leyendo E0.0: {e}")
    
    # Test writing digital output
    print("\n✍️ Probando escritura A0.0...")
    try:
        plc.write_bit("A0.0", True)
        print("✅ A0.0 = ON")
        
        # Read back
        value = plc.read_bit("A0.0")
        print(f"✅ A0.0 leído = {value}")
        
        # Turn off
        plc.write_bit("A0.0", False)
        print("✅ A0.0 = OFF")
        
    except Exception as e:
        print(f"❌ Error escribiendo A0.0: {e}")
    
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