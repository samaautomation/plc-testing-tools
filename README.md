# PLC Testing Tools for Jetson Nano
## Comunicación con PLC Siemens

Herramientas para probar la comunicación entre Jetson Nano (192.168.1.7) y PLC Siemens (192.168.1.5).

## 🚀 Instalación Rápida

```bash
# Clonar el repositorio
git clone https://github.com/samaautomation/plc-testing-tools.git
cd plc-testing-tools

# Instalar dependencias
sudo apt update
sudo apt install python3 python3-pip python3-dev
pip3 install python-snap7

# Probar PLC
cd industrial-siemens-lib/examples
python3 quick_test_plc.py
```

## 📋 Archivos Incluidos

- `industrial-siemens-lib/` - Librería completa para comunicación PLC
- `README-PLC-TESTING.md` - Documentación detallada
- `quick_test_plc.py` - Prueba rápida de conexión
- `plc_io_tester.py` - Prueba completa de I/O

## 🔧 Configuración

- **Jetson Nano:** 192.168.1.7
- **PLC Siemens:** 192.168.1.5
- **Rack:** 0
- **Slot:** 1

## 📞 Soporte

SAMA Engineering - soporte@sama-engineering.com 