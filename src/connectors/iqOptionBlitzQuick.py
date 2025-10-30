#!/usr/bin/env python3
"""
IQ Option Blitz Quick - Operaciones rápidas usando pyautogui
"""

import sys
import json
import time
import logging
import pyautogui

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class IQOptionBlitzQuick:
    def __init__(self):
        # Configurar pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
    def find_and_click_button(self, button_text, x=None, y=None):
        """Hacer clic en coordenadas específicas"""
        try:
            logging.info(f"🔍 Haciendo clic en botón: {button_text}")
            
            # Usar coordenadas calibradas
            if x is None or y is None:
                # Coordenadas calibradas correctas de tu pantalla
                x, y = 1221, 325  # Posición real del botón Blitz
            
            logging.info(f"🖱️ Haciendo clic en ({x}, {y})")
            pyautogui.click(x, y)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error haciendo clic: {e}")
            return False
    
    def execute_blitz_trade(self, direction):
        """Ejecutar operación Blitz usando pyautogui"""
        try:
            logging.info(f"🎯 Ejecutando Blitz {direction.upper()} usando clics automáticos")
            
            # Enfocar ventana de Chrome (buscar por título)
            windows = pyautogui.getWindowsWithTitle("IQ Option")
            if windows:
                windows[0].activate()
                time.sleep(1)
                logging.info("✅ Ventana IQ Option enfocada")
            else:
                logging.warning("⚠️ No se encontró ventana IQ Option")
            
            # Hacer clic en el botón correspondiente
            if direction.upper() in ["CALL", "HIGHER"]:
                success = self.find_and_click_button("HIGHER")
            else:
                success = self.find_and_click_button("LOWER")
            
            if success:
                logging.info(f"✅ Operación {direction.upper()} ejecutada")
                return {"success": True, "message": f"Blitz {direction.upper()} ejecutado"}
            else:
                return {"success": False, "message": "No se pudo hacer clic"}
                
        except Exception as e:
            logging.error(f"❌ Error ejecutando Blitz: {e}")
            return {"success": False, "message": str(e)}
    
    def calibrate_buttons(self):
        """Ayudar a calibrar las posiciones de los botones"""
        try:
            logging.info("🎯 CALIBRACIÓN - Mueve el mouse sobre el botón HIGHER y presiona ENTER")
            input("Presiona ENTER cuando el mouse esté sobre HIGHER...")
            higher_pos = pyautogui.position()
            logging.info(f"📍 Posición HIGHER: {higher_pos}")
            
            logging.info("🎯 Ahora mueve el mouse sobre el botón LOWER y presiona ENTER")
            input("Presiona ENTER cuando el mouse esté sobre LOWER...")
            lower_pos = pyautogui.position()
            logging.info(f"📍 Posición LOWER: {lower_pos}")
            
            return {
                "higher": higher_pos,
                "lower": lower_pos
            }
            
        except Exception as e:
            logging.error(f"❌ Error en calibración: {e}")
            return None

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Comando requerido"}))
        return
    
    command = sys.argv[1]
    blitz = IQOptionBlitzQuick()
    
    try:
        if command == "buy":
            if len(sys.argv) < 3:
                print(json.dumps({"success": False, "message": "Dirección requerida (call/put)"}))
                return
            
            direction = sys.argv[2]
            result = blitz.execute_blitz_trade(direction)
            print(json.dumps(result))
            
        elif command == "calibrate":
            positions = blitz.calibrate_buttons()
            if positions:
                print(json.dumps({"success": True, "positions": positions}))
            else:
                print(json.dumps({"success": False, "message": "Error en calibración"}))
                
        else:
            print(json.dumps({"success": False, "message": f"Comando desconocido: {command}"}))
            
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))

if __name__ == "__main__":
    main()
