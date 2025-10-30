#!/usr/bin/env python3
"""
Test visual para verificar clics en Blitz
"""

import sys
import json
import time
import logging
import pyautogui

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def test_click_position():
    """Test visual de posición de clic"""
    try:
        logging.info("🎯 TEST VISUAL - En 3 segundos haré clic en la posición calibrada")
        logging.info("   Observa tu pantalla para ver si hace clic en el botón correcto")
        
        # Countdown
        for i in range(3, 0, -1):
            logging.info(f"   {i}...")
            time.sleep(1)
        
        # Enfocar ventana IQ Option
        windows = pyautogui.getWindowsWithTitle("IQ Option")
        if windows:
            windows[0].activate()
            time.sleep(0.5)
            logging.info("✅ Ventana IQ Option enfocada")
        
        # Hacer clic en la posición calibrada
        x, y = 505, 683
        logging.info(f"🖱️ HACIENDO CLIC EN ({x}, {y}) - ¡OBSERVA TU PANTALLA!")
        
        # Mover mouse primero para que veas dónde va a hacer clic
        pyautogui.moveTo(x, y, duration=1)
        time.sleep(1)
        
        # Hacer el clic
        pyautogui.click(x, y)
        
        logging.info("✅ Clic ejecutado")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error en test: {e}")
        return False

def get_mouse_position():
    """Obtener posición actual del mouse"""
    try:
        pos = pyautogui.position()
        logging.info(f"📍 Posición actual del mouse: {pos}")
        return pos
    except Exception as e:
        logging.error(f"❌ Error obteniendo posición: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Uso: python script.py [test|position]")
        return
    
    command = sys.argv[1]
    
    if command == "test":
        success = test_click_position()
        print(json.dumps({"success": success}))
    elif command == "position":
        pos = get_mouse_position()
        if pos:
            print(json.dumps({"success": True, "position": [pos.x, pos.y]}))
        else:
            print(json.dumps({"success": False}))
    else:
        print(json.dumps({"success": False, "message": "Comando desconocido"}))

if __name__ == "__main__":
    main()
