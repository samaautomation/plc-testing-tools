#!/usr/bin/env python3
"""
Prueba Rápida PLC Siemens - IP: 192.168.1.5
============================================

Script simple para probar conexión y I/O básico con PLC Siemens
desde Jetson Nano.

Autor: SAMA Engineering
"""

import sys
import time
from datetime import datetime

# Agregar el directorio padre al path para importar la librería
sys.path.append('..')

try:
    from siemens_plc.connection import SiemensPLCConnection
    from siemens_plc.exceptions import PLCConnectionError
    print("✅ Librería Siemens PLC importada correctamente")
except ImportError as e:
    print(f"❌ Error importando librería: {e}")
    print("Asegúrate de estar en el directorio correcto")
    sys.exit(1)

def test_connection():
    """Probar conexión al PLC"""
    print("\n🔌 PROBANDO CONEXIÓN AL PLC")
    print("=" * 40)
    print(f"IP del PLC: 192.168.1.5")
    print(f"Rack: 0, Slot: 1")
    print("=" * 40)
    
    try:
            # Crear conexión
    plc = SiemensPLCConnection(
        ip_address="192.168.1.5",  # IP del PLC Siemens
        rack=0,
        slot=1,
        auto_reconnect=True,
        heartbeat_interval=5.0
    )
        
        print("📡 Conectando al PLC...")
        plc.connect()
        print("✅ ¡CONEXIÓN EXITOSA!")
        
        return plc
        
    except PLCConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        print("\n🔍 Posibles causas:")
        print("   - PLC no está encendido")
        print("   - IP incorrecta")
        print("   - Red no configurada")
        print("   - Firewall bloqueando")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def test_digital_io(plc):
    """Probar entradas y salidas digitales"""
    print("\n🔌 PROBANDO I/O DIGITAL")
    print("=" * 40)
    
    # Probar lectura de entrada digital
    try:
        print("📖 Leyendo entrada digital E0.0...")
        value = plc.read_bit("E0.0")
        print(f"✅ E0.0 = {value} ({'ON' if value else 'OFF'})")
    except Exception as e:
        print(f"❌ Error leyendo E0.0: {e}")
    
    # Probar escritura de salida digital
    try:
        print("\n✍️ Probando salida digital A0.0...")
        print("   Encendiendo A0.0...")
        plc.write_bit("A0.0", True)
        time.sleep(1)
        
        print("   Apagando A0.0...")
        plc.write_bit("A0.0", False)
        print("✅ Escritura de salida digital exitosa")
    except Exception as e:
        print(f"❌ Error escribiendo A0.0: {e}")

def test_analog_io(plc):
    """Probar entradas y salidas analógicas"""
    print("\n📊 PROBANDO I/O ANALÓGICO")
    print("=" * 40)
    
    # Probar lectura de entrada analógica
    try:
        print("📖 Leyendo entrada analógica IW64...")
        value = plc.read_word("IW64")
        print(f"✅ IW64 = {value}")
    except Exception as e:
        print(f"❌ Error leyendo IW64: {e}")
    
    # Probar escritura de salida analógica
    try:
        print("\n✍️ Probando salida analógica QW80...")
        test_value = 1234
        print(f"   Escribiendo QW80 = {test_value}...")
        plc.write_word("QW80", test_value)
        print("✅ Escritura de salida analógica exitosa")
    except Exception as e:
        print(f"❌ Error escribiendo QW80: {e}")

def test_marks(plc):
    """Probar marcas (memoria interna)"""
    print("\n🏷️ PROBANDO MARCAS")
    print("=" * 40)
    
    try:
        print("📖 Leyendo marca M0.0...")
        value = plc.read_bit("M0.0")
        print(f"✅ M0.0 = {value} ({'ON' if value else 'OFF'})")
        
        print("\n✍️ Escribiendo marca M0.1...")
        plc.write_bit("M0.1", True)
        print("✅ Escritura de marca exitosa")
    except Exception as e:
        print(f"❌ Error con marcas: {e}")

def test_data_blocks(plc):
    """Probar bloques de datos"""
    print("\n💾 PROBANDO BLOQUES DE DATOS")
    print("=" * 40)
    
    try:
        print("📖 Leyendo DB1.DBW0...")
        value = plc.read_word("DB1.DBW0")
        print(f"✅ DB1.DBW0 = {value}")
        
        print("\n✍️ Escribiendo DB1.DBW2...")
        test_value = 5678
        plc.write_word("DB1.DBW2", test_value)
        print(f"✅ Escrito DB1.DBW2 = {test_value}")
    except Exception as e:
        print(f"❌ Error con bloques de datos: {e}")

def main():
    """Función principal"""
    print("🚀 PRUEBA RÁPIDA PLC SIEMENS - JETSON NANO")
    print("=" * 50)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Probar conexión
    plc = test_connection()
    
    if plc is None:
        print("\n❌ No se pudo conectar al PLC")
        print("Revisa la configuración de red y la IP del PLC")
        return
    
    try:
        # Probar diferentes tipos de I/O
        test_digital_io(plc)
        test_analog_io(plc)
        test_marks(plc)
        test_data_blocks(plc)
        
        print("\n" + "=" * 50)
        print("🎉 ¡PRUEBA COMPLETADA EXITOSAMENTE!")
        print("=" * 50)
        
        # Preguntar si continuar con monitoreo
        response = input("\n¿Quieres iniciar monitoreo en tiempo real? (s/n): ").lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            print("\n🔄 Iniciando monitoreo... (Ctrl+C para detener)")
            monitor_loop(plc)
    
    except KeyboardInterrupt:
        print("\n⏹️ Detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
    finally:
        if plc:
            plc.disconnect()
            print("✅ Conexión cerrada")

def monitor_loop(plc):
    """Loop de monitoreo simple"""
    try:
        while True:
            print("\n" + "=" * 40)
            print(f"📊 MONITOREO - {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 40)
            
            # Leer entradas digitales
            try:
                e0_0 = plc.read_bit("E0.0")
                e0_1 = plc.read_bit("E0.1")
                print(f"🔌 E0.0: {'🟢 ON' if e0_0 else '🔴 OFF'} | E0.1: {'🟢 ON' if e0_1 else '🔴 OFF'}")
            except:
                print("🔌 E0.0: ❌ ERROR | E0.1: ❌ ERROR")
            
            # Leer entrada analógica
            try:
                iw64 = plc.read_word("IW64")
                print(f"📊 IW64: {iw64}")
            except:
                print("📊 IW64: ❌ ERROR")
            
            # Leer marca
            try:
                m0_0 = plc.read_bit("M0.0")
                print(f"🏷️ M0.0: {'🟢 ON' if m0_0 else '🔴 OFF'}")
            except:
                print("🏷️ M0.0: ❌ ERROR")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n⏹️ Monitoreo detenido")

if __name__ == "__main__":
    main() 