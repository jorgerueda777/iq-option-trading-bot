#!/usr/bin/env python3
"""
Quotex Smart Detector - Detecta automáticamente todos los pares con payout alto
Busca pares con 90%+ de payout en 1 minuto
"""

import sys
import json
import time
import logging
import re
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexSmartDetector:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.available_pairs = []
        self.high_payout_pairs = []
        
    def setup_chrome(self):
        """Configurar Chrome"""
        try:
            logging.info("🛡️ Configurando Chrome...")
            
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.maximize_window()
            
            logging.info("✅ Chrome configurado")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            return False
    
    def open_quotex(self):
        """Abrir Quotex"""
        try:
            logging.info("🌐 Abriendo Quotex...")
            self.driver.get("https://qxbroker.com/")
            time.sleep(3)
            
            logging.info("👤 HAZ LOGIN - 60 segundos")
            time.sleep(60)
            
            current_url = self.driver.current_url
            if "qxbroker.com" in current_url:
                logging.info("✅ Login exitoso")
                self.logged_in = True
                return True
            return False
                
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            return False
    
    def scan_all_pairs(self):
        """Escanear TODOS los pares disponibles en Quotex"""
        try:
            logging.info("🔍 ESCANEANDO TODOS LOS PARES DISPONIBLES...")
            
            # Buscar elementos que contengan información de pares y payouts
            pair_elements = self.driver.find_elements(By.XPATH, "//*")
            
            pairs_found = {}
            
            for element in pair_elements:
                try:
                    text = element.text.strip()
                    if not text or len(text) > 100:
                        continue
                    
                    # Buscar patrones de pares de divisas
                    pair_patterns = [
                        r'([A-Z]{3})/([A-Z]{3})',  # EUR/USD
                        r'([A-Z]{6})',             # EURUSD
                        r'([A-Z]{3})([A-Z]{3})'    # EURUSD sin separador
                    ]
                    
                    for pattern in pair_patterns:
                        matches = re.findall(pattern, text)
                        for match in matches:
                            if isinstance(match, tuple):
                                pair = ''.join(match)
                            else:
                                pair = match
                            
                            # Validar que sea un par de divisas real
                            currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD', 'BRL', 'MXN', 'ZAR']
                            if len(pair) == 6:
                                base = pair[:3]
                                quote = pair[3:]
                                if base in currencies and quote in currencies and base != quote:
                                    # Buscar payout en el mismo elemento o elementos cercanos
                                    payout = self.extract_payout_from_element(element)
                                    if payout:
                                        pairs_found[pair] = payout
                                        logging.info(f"💱 {pair}: {payout}%")
                
                except Exception as e:
                    continue
            
            self.available_pairs = pairs_found
            logging.info(f"📊 Total pares encontrados: {len(pairs_found)}")
            
            return pairs_found
            
        except Exception as e:
            logging.error(f"❌ Error escaneando pares: {e}")
            return {}
    
    def extract_payout_from_element(self, element):
        """Extraer payout de un elemento"""
        try:
            # Buscar porcentajes en el texto del elemento
            text = element.text
            payout_patterns = [
                r'(\d{1,3})%',
                r'(\d{1,3})\s*%',
                r'(\d{1,3})\s*percent'
            ]
            
            for pattern in payout_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    payout = int(match)
                    if 50 <= payout <= 100:  # Rango válido de payout
                        return payout
            
            # Buscar en elementos padre/hijo
            try:
                parent = element.find_element(By.XPATH, "..")
                parent_text = parent.text
                for pattern in payout_patterns:
                    matches = re.findall(pattern, parent_text)
                    for match in matches:
                        payout = int(match)
                        if 50 <= payout <= 100:
                            return payout
            except:
                pass
            
            # Buscar en elementos hermanos
            try:
                siblings = element.find_elements(By.XPATH, "../*")
                for sibling in siblings:
                    sibling_text = sibling.text
                    for pattern in payout_patterns:
                        matches = re.findall(pattern, sibling_text)
                        for match in matches:
                            payout = int(match)
                            if 50 <= payout <= 100:
                                return payout
            except:
                pass
                
            return None
            
        except Exception as e:
            return None
    
    def filter_high_payout_pairs(self, min_payout=90):
        """Filtrar pares con payout alto"""
        try:
            logging.info(f"🎯 FILTRANDO PARES CON PAYOUT {min_payout}%+...")
            
            high_payout = {}
            
            for pair, payout in self.available_pairs.items():
                if payout >= min_payout:
                    high_payout[pair] = payout
                    logging.info(f"🔥 {pair}: {payout}% ✅")
            
            self.high_payout_pairs = high_payout
            
            if high_payout:
                logging.info(f"🎉 {len(high_payout)} pares con payout {min_payout}%+:")
                for pair, payout in sorted(high_payout.items(), key=lambda x: x[1], reverse=True):
                    logging.info(f"   🏆 {pair}: {payout}%")
            else:
                logging.warning(f"⚠️ No se encontraron pares con payout {min_payout}%+")
            
            return high_payout
            
        except Exception as e:
            logging.error(f"❌ Error filtrando pares: {e}")
            return {}
    
    def scan_specific_timeframes(self):
        """Escanear payouts específicos para 1 minuto"""
        try:
            logging.info("⏰ ESCANEANDO PAYOUTS PARA 1 MINUTO...")
            
            # Buscar elementos que indiquen timeframe de 1 minuto
            timeframe_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '1m') or contains(text(), '1 min') or contains(text(), '60s')]")
            
            one_minute_pairs = {}
            
            for element in timeframe_elements:
                try:
                    # Buscar pares cerca de este elemento de timeframe
                    parent = element.find_element(By.XPATH, "../..")
                    parent_text = parent.text
                    
                    # Extraer par y payout del contexto
                    pair_match = re.search(r'([A-Z]{6})', parent_text)
                    payout_match = re.search(r'(\d{1,3})%', parent_text)
                    
                    if pair_match and payout_match:
                        pair = pair_match.group(1)
                        payout = int(payout_match.group(1))
                        
                        if payout >= 90:
                            one_minute_pairs[pair] = payout
                            logging.info(f"⏰ 1min - {pair}: {payout}%")
                
                except:
                    continue
            
            return one_minute_pairs
            
        except Exception as e:
            logging.error(f"❌ Error escaneando timeframes: {e}")
            return {}
    
    def get_best_pairs_for_trading(self, min_payout=90):
        """Obtener los mejores pares para trading"""
        try:
            logging.info("🚀 INICIANDO ESCANEO COMPLETO...")
            
            # Escanear todos los pares
            all_pairs = self.scan_all_pairs()
            
            # Filtrar por payout alto
            high_payout = self.filter_high_payout_pairs(min_payout)
            
            # Escanear timeframes específicos
            one_min_pairs = self.scan_specific_timeframes()
            
            # Combinar resultados
            best_pairs = {}
            
            # Priorizar pares de 1 minuto con alto payout
            for pair, payout in one_min_pairs.items():
                best_pairs[pair] = {
                    'payout': payout,
                    'timeframe': '1m',
                    'priority': 'HIGH'
                }
            
            # Agregar otros pares con alto payout
            for pair, payout in high_payout.items():
                if pair not in best_pairs:
                    best_pairs[pair] = {
                        'payout': payout,
                        'timeframe': 'unknown',
                        'priority': 'MEDIUM'
                    }
            
            # Mostrar resultados finales
            logging.info("🏆 MEJORES PARES PARA TRADING:")
            logging.info("=" * 50)
            
            if best_pairs:
                for pair, info in sorted(best_pairs.items(), key=lambda x: x[1]['payout'], reverse=True):
                    priority_emoji = "🔥" if info['priority'] == 'HIGH' else "⭐"
                    logging.info(f"{priority_emoji} {pair}: {info['payout']}% ({info['timeframe']})")
            else:
                logging.warning("⚠️ No se encontraron pares con payout alto")
            
            logging.info("=" * 50)
            
            return best_pairs
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo mejores pares: {e}")
            return {}
    
    def close(self):
        """Cerrar navegador"""
        if self.driver:
            self.driver.quit()

def main():
    """Función principal"""
    detector = QuotexSmartDetector()
    
    try:
        # Setup
        if not detector.setup_chrome():
            return
        
        if not detector.open_quotex():
            return
        
        # Obtener mejores pares
        best_pairs = detector.get_best_pairs_for_trading(min_payout=90)
        
        # Mostrar resultado JSON
        result = {
            "success": True,
            "total_pairs": len(best_pairs),
            "high_payout_pairs": best_pairs,
            "timestamp": datetime.now().isoformat()
        }
        
        print(json.dumps(result, indent=2))
        
        # Mantener abierto para más análisis
        logging.info("🤖 Detector listo para más análisis...")
        logging.info("💡 Comandos disponibles:")
        logging.info("   - 'scan' = Escanear de nuevo")
        logging.info("   - 'filter X' = Filtrar por payout X%")
        logging.info("   - 'q' = Salir")
        
        while True:
            try:
                command = input("\n🎯 Comando: ").strip().lower()
                
                if command in ['q', 'quit', 'exit']:
                    logging.info("👋 Cerrando detector...")
                    break
                elif command == 'scan':
                    detector.get_best_pairs_for_trading(90)
                elif command.startswith('filter'):
                    try:
                        payout = int(command.split()[1])
                        detector.filter_high_payout_pairs(payout)
                    except:
                        logging.info("❓ Uso: filter 90")
                else:
                    logging.info("❓ Comando no reconocido")
                    
            except KeyboardInterrupt:
                logging.info("\n👋 Detector cerrado por usuario")
                break
        
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))
    finally:
        detector.close()

if __name__ == "__main__":
    main()
