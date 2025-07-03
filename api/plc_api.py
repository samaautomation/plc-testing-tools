#!/usr/bin/env python3
"""
PLC API for SAMABOT UI Light
============================

API Flask para comunicación con PLC Siemens que puede ser integrado
con la interfaz web de SAMABOT UI Light.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import threading
import time

# Agregar el directorio de la librería al path
sys.path.append('../industrial-siemens-lib/examples')

from plc_service import PLCService

app = Flask(__name__)
CORS(app)  # Permitir CORS para la interfaz web

# Variable global para el servicio PLC
plc_service = None
plc_lock = threading.Lock()

def get_plc_service():
    """Obtiene o crea el servicio PLC."""
    global plc_service
    with plc_lock:
        if plc_service is None:
            plc_service = PLCService()
        return plc_service

@app.route('/api/plc/status', methods=['GET'])
def get_plc_status():
    """Obtiene el estado actual del PLC."""
    try:
        plc = get_plc_service()
        data = plc.get_data()
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/plc/connect', methods=['POST'])
def connect_plc():
    """Conecta al PLC."""
    try:
        plc = get_plc_service()
        success = plc.connect()
        
        if success:
            plc.start_monitoring()
            return jsonify({
                "success": True,
                "message": "PLC conectado exitosamente"
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo conectar al PLC"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/plc/disconnect', methods=['POST'])
def disconnect_plc():
    """Desconecta del PLC."""
    try:
        plc = get_plc_service()
        plc.disconnect()
        return jsonify({
            "success": True,
            "message": "PLC desconectado"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/plc/output', methods=['POST'])
def write_output():
    """Escribe una salida digital."""
    try:
        data = request.get_json()
        output = data.get('output')
        value = data.get('value')
        
        if output is None or value is None:
            return jsonify({
                "success": False,
                "error": "Se requiere 'output' y 'value'"
            }), 400
        
        plc = get_plc_service()
        success = plc.write_output(output, bool(value))
        
        if success:
            return jsonify({
                "success": True,
                "message": f"{output} = {'ON' if value else 'OFF'}"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"No se pudo escribir {output}"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/plc/outputs', methods=['POST'])
def write_multiple_outputs():
    """Escribe múltiples salidas digitales."""
    try:
        data = request.get_json()
        outputs = data.get('outputs', {})
        
        if not outputs:
            return jsonify({
                "success": False,
                "error": "Se requiere 'outputs' con formato {'A0.0': true, 'A0.1': false}"
            }), 400
        
        plc = get_plc_service()
        results = {}
        
        for output, value in outputs.items():
            success = plc.write_output(output, bool(value))
            results[output] = success
        
        return jsonify({
            "success": True,
            "results": results
        })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/plc/inputs', methods=['GET'])
def get_inputs():
    """Obtiene el estado de las entradas digitales."""
    try:
        plc = get_plc_service()
        data = plc.get_data()
        return jsonify({
            "success": True,
            "data": data['inputs']
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/plc/outputs', methods=['GET'])
def get_outputs():
    """Obtiene el estado de las salidas digitales."""
    try:
        plc = get_plc_service()
        data = plc.get_data()
        return jsonify({
            "success": True,
            "data": data['outputs']
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/plc/analog', methods=['GET'])
def get_analog():
    """Obtiene los valores analógicos."""
    try:
        plc = get_plc_service()
        data = plc.get_data()
        return jsonify({
            "success": True,
            "data": data['analog']
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/plc/config', methods=['POST'])
def update_config():
    """Actualiza la configuración del PLC."""
    try:
        data = request.get_json()
        ip = data.get('ip', '192.168.1.5')
        rack = data.get('rack', 0)
        slot = data.get('slot', 1)
        
        global plc_service
        with plc_lock:
            if plc_service:
                plc_service.disconnect()
            plc_service = PLCService(ip, rack, slot)
        
        return jsonify({
            "success": True,
            "message": f"Configuración actualizada: {ip}:{rack}:{slot}"
        })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/plc/health', methods=['GET'])
def health_check():
    """Health check del API."""
    try:
        plc = get_plc_service()
        data = plc.get_data()
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "plc_connected": data['connection']['status'] == 'connected',
            "uptime": data['connection']['uptime'],
            "last_update": data['connection']['last_update']
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Iniciando PLC API...")
    print("📡 Endpoints disponibles:")
    print("  GET  /api/plc/status     - Estado completo del PLC")
    print("  POST /api/plc/connect    - Conectar al PLC")
    print("  POST /api/plc/disconnect - Desconectar del PLC")
    print("  POST /api/plc/output     - Escribir salida digital")
    print("  GET  /api/plc/inputs     - Leer entradas digitales")
    print("  GET  /api/plc/outputs    - Leer salidas digitales")
    print("  GET  /api/plc/analog     - Leer valores analógicos")
    print("  POST /api/plc/config     - Actualizar configuración")
    print("  GET  /api/plc/health     - Health check")
    print("\n🌐 API iniciada en http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 