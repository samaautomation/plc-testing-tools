# Pruebas PLC Siemens - Jetson Nano
## IP del PLC: 192.168.1.5

Este documento explica cómo probar la comunicación entre el Jetson Nano y un PLC Siemens con IP `192.168.1.5`.

## 📋 Requisitos Previos

### En el Jetson Nano:
- Ubuntu 18.04 o superior
- Python 3.6+
- pip3
- Conexión de red al PLC

### En el PLC Siemens:
- IP configurada: `192.168.1.5`
- Comunicación S7 habilitada
- Rack: 0, Slot: 1 (configuración por defecto)

## 🚀 Instalación Rápida

### 1. Verificar Dependencias
```bash
# En el Jetson Nano
sudo apt update
sudo apt install python3 python3-pip python3-dev

# Instalar snap7
pip3 install python-snap7
```

### 2. Clonar/Descargar el Proyecto
```bash
# Si tienes el proyecto completo
cd samabot-ui-light

# O descargar solo la librería industrial
git clone <tu-repo> industrial-siemens-lib
cd industrial-siemens-lib
```

## 🔧 Pruebas Disponibles

### Opción 1: Prueba Rápida (Recomendada)
```bash
# Desde el directorio raíz del proyecto
cd industrial-siemens-lib/examples
python3 quick_test_plc.py
```

**Esta prueba:**
- ✅ Verifica la conexión al PLC
- ✅ Prueba lectura de entradas digitales (E0.0)
- ✅ Prueba escritura de salidas digitales (A0.0)
- ✅ Prueba entradas/salidas analógicas (IW64/QW80)
- ✅ Prueba marcas y bloques de datos
- ✅ Ofrece monitoreo en tiempo real

### Opción 2: Prueba Completa
```bash
cd industrial-siemens-lib/examples
python3 plc_io_tester.py
```

**Esta prueba incluye:**
- 🔌 8 entradas digitales (E0.0 - E0.7)
- 🔌 8 salidas digitales (A0.0 - A0.7)
- 📊 4 entradas analógicas (IW64, IW66, IW68, IW70)
- 📊 4 salidas analógicas (QW80, QW82, QW84, QW86)
- 🏷️ 8 marcas (M0.0 - M0.7)
- 💾 4 bloques de datos (DB1.DBW0, DB1.DBW2, DB1.DBW4, DB1.DBW6)

### Opción 3: Script Interactivo (Jetson)
```bash
# Hacer ejecutable el script (en Linux/Jetson)
chmod +x scripts/test-plc-jetson.sh

# Ejecutar
./scripts/test-plc-jetson.sh
```

## 🔍 Diagnóstico de Problemas

### 1. Verificar Conectividad de Red
```bash
# Hacer ping al PLC
ping 192.168.1.5

# Verificar configuración de red
ip addr show
ip route show
```

### 2. Verificar Configuración del PLC
- ✅ IP del PLC: `192.168.1.5`
- ✅ Rack: `0`
- ✅ Slot: `1`
- ✅ Comunicación S7 habilitada
- ✅ Firewall deshabilitado o puerto 102 abierto

### 3. Errores Comunes

#### Error: "Connection failed"
```
❌ Error de conexión: Connection failed
```
**Soluciones:**
- Verificar que el PLC esté encendido
- Verificar la IP del PLC
- Verificar la configuración de red del Jetson
- Verificar que ambos dispositivos estén en la misma red

#### Error: "Read failed"
```
❌ Error leyendo E0.0: Read failed
```
**Soluciones:**
- Verificar que la dirección E0.0 exista en el PLC
- Verificar que el programa del PLC esté ejecutándose
- Verificar permisos de lectura

#### Error: "Write failed"
```
❌ Error escribiendo A0.0: Write failed
```
**Soluciones:**
- Verificar que la dirección A0.0 exista en el PLC
- Verificar que no esté protegida contra escritura
- Verificar que el PLC esté en modo RUN

## 📊 Monitoreo en Tiempo Real

### Iniciar Monitoreo
```bash
cd industrial-siemens-lib/examples
python3 quick_test_plc.py
# Seleccionar "s" cuando pregunte por monitoreo
```

### Salida del Monitoreo
```
========================================
📊 MONITOREO - 14:30:25
========================================
🔌 E0.0: 🟢 ON | E0.1: 🔴 OFF
📊 IW64: 1234
🏷️ M0.0: 🟢 ON
========================================
```

## 🔧 Configuración Avanzada

### Cambiar IP del PLC
Editar el archivo `quick_test_plc.py`:
```python
plc = SiemensPLCConnection(
    ip_address="192.168.1.5",  # Cambiar aquí
    rack=0,
    slot=1,
    auto_reconnect=True,
    heartbeat_interval=5.0
)
```

### Cambiar Direcciones de I/O
Editar el archivo `plc_io_tester.py` en la sección `test_areas`:
```python
self.test_areas = {
    'digital_inputs': {
        'E0.0': 'Entrada Digital 0',  # Cambiar direcciones aquí
        'E0.1': 'Entrada Digital 1',
        # ...
    }
}
```

## 📝 Logs y Resultados

### Archivos de Log
- `plc_io_tester.log`: Log detallado de todas las operaciones
- `plc_test_results_YYYYMMDD_HHMMSS.json`: Resultados exportados

### Exportar Resultados
```python
# En el script de prueba
tester.export_results("mi_prueba_plc.json")
```

## 🎯 Ejemplos de Uso

### Ejemplo 1: Prueba Básica de Conexión
```bash
cd industrial-siemens-lib/examples
python3 quick_test_plc.py
```

### Ejemplo 2: Monitoreo Continuo
```bash
cd industrial-siemens-lib/examples
python3 -c "
import sys
sys.path.append('..')
from plc_io_tester import PLCIOTester, IOTestConfig
config = IOTestConfig(plc_ip='192.168.1.5')
tester = PLCIOTester(config)
tester.connect()
tester.start_monitoring()
try:
    while True:
        import time
        time.sleep(1)
except KeyboardInterrupt:
    tester.stop_monitoring()
    tester.disconnect()
"
```

### Ejemplo 3: Prueba Específica de I/O
```python
from siemens_plc.connection import SiemensPLCConnection

# Conectar al PLC
plc = SiemensPLCConnection("192.168.1.5", 0, 1)
plc.connect()

# Leer entrada digital
value = plc.read_bit("E0.0")
print(f"E0.0 = {value}")

# Escribir salida digital
plc.write_bit("A0.0", True)

# Leer entrada analógica
value = plc.read_word("IW64")
print(f"IW64 = {value}")

# Cerrar conexión
plc.disconnect()
```

## 🔒 Seguridad

### Recomendaciones
- ✅ Usar red dedicada para comunicación industrial
- ✅ Configurar firewall apropiadamente
- ✅ Usar credenciales seguras si están disponibles
- ✅ Monitorear logs de acceso

### Puertos Utilizados
- **Puerto 102**: Comunicación S7 (TCP)
- **Puerto 161/162**: SNMP (opcional)

## 📞 Soporte

### Información de Contacto
- **SAMA Engineering**
- **Email**: soporte@sama-engineering.com
- **Documentación**: [Enlace al repositorio]

### Información del Sistema
- **PLC**: Siemens S7-1200/1500
- **IP**: 192.168.1.5
- **Protocolo**: S7 Communication
- **Jetson**: Nano/TX2/Xavier

---

**Nota**: Asegúrate de que el PLC esté configurado correctamente y que las direcciones de I/O existan en tu programa del PLC antes de ejecutar las pruebas. 