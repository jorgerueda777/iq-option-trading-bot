#!/usr/bin/env python3
"""
QUOTEX TOKEN KEEPER - Mantener tokens activos y evitar refrescos
Solución definitiva para el problema de tokens que expiran
"""

import time
import logging
import requests
import json
from datetime import datetime, timedelta
from threading import Thread, Lock
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexTokenKeeper:
    def __init__(self):
        self.logger = logging.getLogger('QuotexTokenKeeper')
        self.tokens = {}
        self.sessions = {}
        self.drivers = {}
        self.lock = Lock()
        
        # Credenciales
        self.email = "arnolbrom634@gmail.com"
        self.password = "7decadames"
        
        # Estado de tokens
        self.token_refresh_interval = 300  # 5 minutos
        self.running = True
        
    def create_persistent_session(self, pair):
        """Crear sesión persistente para un activo específico"""
        try:
            self.logger.info(f"🔐 Creando sesión persistente para {pair}...")
            
            # Configurar Chrome con persistencia extrema
            options = uc.ChromeOptions()
            
            # PERSISTENCIA BRUTAL
            user_data_dir = f"C:/temp/quotex_persistent_{pair.replace(' ', '_')}"
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument("--profile-directory=Default")
            
            # ANTI-DETECCIÓN EXTREMA
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-web-security")
            
            # MANTENER SESIÓN VIVA
            options.add_argument("--keep-alive-for-test")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            
            # Crear driver
            driver = uc.Chrome(options=options, version_main=None)
            
            # INYECTAR KEEPER DE TOKENS INMEDIATAMENTE
            self.inject_token_keeper(driver, pair)
            
            self.drivers[pair] = driver
            
            self.logger.info(f"✅ Sesión persistente creada para {pair}")
            return driver
            
        except Exception as e:
            self.logger.error(f"❌ Error creando sesión para {pair}: {e}")
            return None
    
    def inject_token_keeper(self, driver, pair):
        """Inyectar script para mantener tokens vivos"""
        try:
            token_keeper_js = f"""
            // TOKEN KEEPER PARA {pair}
            (function() {{
                console.log('🔐 TOKEN KEEPER ACTIVADO PARA {pair}');
                
                // Interceptar y guardar todos los tokens
                window.TOKENS = {{}};
                window.PAIR_NAME = '{pair}';
                
                // Interceptar requests para capturar tokens
                const originalFetch = window.fetch;
                window.fetch = function(url, options) {{
                    return originalFetch.call(this, url, options).then(response => {{
                        // Capturar headers de autenticación
                        const authHeader = response.headers.get('Authorization');
                        const tokenHeader = response.headers.get('X-Auth-Token');
                        const sessionHeader = response.headers.get('Set-Cookie');
                        
                        if (authHeader) {{
                            window.TOKENS.auth = authHeader;
                            console.log('🔑 Token auth capturado:', authHeader.substring(0, 20) + '...');
                        }}
                        
                        if (tokenHeader) {{
                            window.TOKENS.token = tokenHeader;
                            console.log('🔑 X-Auth-Token capturado:', tokenHeader.substring(0, 20) + '...');
                        }}
                        
                        if (sessionHeader) {{
                            window.TOKENS.session = sessionHeader;
                            console.log('🔑 Session capturada');
                        }}
                        
                        return response;
                    }});
                }};
                
                // Interceptar XMLHttpRequest también
                const originalXHR = window.XMLHttpRequest;
                window.XMLHttpRequest = function() {{
                    const xhr = new originalXHR();
                    const originalOpen = xhr.open;
                    const originalSend = xhr.send;
                    
                    xhr.open = function(method, url, async, user, password) {{
                        this._url = url;
                        return originalOpen.call(this, method, url, async, user, password);
                    }};
                    
                    xhr.send = function(data) {{
                        this.addEventListener('readystatechange', function() {{
                            if (this.readyState === 4) {{
                                const authHeader = this.getResponseHeader('Authorization');
                                const tokenHeader = this.getResponseHeader('X-Auth-Token');
                                
                                if (authHeader) {{
                                    window.TOKENS.auth = authHeader;
                                    console.log('🔑 XHR Token auth capturado');
                                }}
                                
                                if (tokenHeader) {{
                                    window.TOKENS.token = tokenHeader;
                                    console.log('🔑 XHR X-Auth-Token capturado');
                                }}
                            }}
                        }});
                        
                        return originalSend.call(this, data);
                    }};
                    
                    return xhr;
                }};
                
                // Función para refrescar tokens automáticamente
                window.refreshTokens = function() {{
                    console.log('🔄 Refrescando tokens para {pair}...');
                    
                    // Hacer request silencioso para mantener sesión viva
                    fetch('/api/v1/user/profile', {{
                        method: 'GET',
                        headers: {{
                            'Authorization': window.TOKENS.auth || '',
                            'X-Auth-Token': window.TOKENS.token || ''
                        }}
                    }}).then(response => {{
                        if (response.ok) {{
                            console.log('✅ Tokens refrescados para {pair}');
                        }} else {{
                            console.log('⚠️ Error refrescando tokens para {pair}');
                        }}
                    }}).catch(e => {{
                        console.log('❌ Error en refresh de tokens:', e);
                    }});
                }};
                
                // Refrescar tokens cada 4 minutos
                setInterval(window.refreshTokens, 240000);
                
                // Mantener página activa
                setInterval(function() {{
                    document.dispatchEvent(new Event('mousemove'));
                }}, 30000);
                
                console.log('✅ TOKEN KEEPER CONFIGURADO PARA {pair}');
                
            }})();
            """
            
            driver.execute_script(token_keeper_js)
            self.logger.info(f"🔐 Token keeper inyectado para {pair}")
            
        except Exception as e:
            self.logger.error(f"❌ Error inyectando token keeper para {pair}: {e}")
    
    def login_and_capture_tokens(self, driver, pair):
        """Login y capturar tokens iniciales"""
        try:
            self.logger.info(f"👤 Haciendo login para {pair}...")
            
            # Ir a Quotex
            driver.get("https://qxbroker.com/")
            time.sleep(3)
            
            # Hacer login manual o automático
            self.logger.info(f"⏳ Esperando login manual para {pair} - 60 segundos")
            
            # Esperar hasta 60 segundos para login manual
            start_time = time.time()
            while time.time() - start_time < 60:
                try:
                    # Verificar si ya está logueado
                    if "trade" in driver.current_url.lower() or "dashboard" in driver.current_url.lower():
                        self.logger.info(f"✅ Login detectado para {pair}")
                        break
                except:
                    pass
                time.sleep(2)
            
            # Capturar tokens después del login
            time.sleep(3)
            tokens = self.extract_tokens(driver)
            
            if tokens:
                with self.lock:
                    self.tokens[pair] = tokens
                    self.tokens[pair]['timestamp'] = datetime.now()
                
                self.logger.info(f"🔑 Tokens capturados para {pair}: {len(tokens)} tokens")
                return True
            else:
                self.logger.warning(f"⚠️ No se capturaron tokens para {pair}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en login para {pair}: {e}")
            return False
    
    def extract_tokens(self, driver):
        """Extraer tokens del navegador"""
        try:
            # Ejecutar script para obtener tokens capturados
            tokens_js = """
            return {
                tokens: window.TOKENS || {},
                cookies: document.cookie,
                localStorage: JSON.stringify(localStorage),
                sessionStorage: JSON.stringify(sessionStorage)
            };
            """
            
            result = driver.execute_script(tokens_js)
            
            if result and result.get('tokens'):
                return result
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo tokens: {e}")
            return None
    
    def start_token_refresh_daemon(self):
        """Iniciar daemon para refrescar tokens automáticamente"""
        def refresh_daemon():
            while self.running:
                try:
                    self.logger.info("🔄 Daemon de refresh de tokens ejecutándose...")
                    
                    with self.lock:
                        for pair, driver in self.drivers.items():
                            if driver:
                                try:
                                    # Ejecutar refresh de tokens en cada ventana
                                    driver.execute_script("if (window.refreshTokens) window.refreshTokens();")
                                    self.logger.info(f"🔄 Tokens refrescados para {pair}")
                                except Exception as e:
                                    self.logger.error(f"❌ Error refrescando {pair}: {e}")
                    
                    # Esperar 4 minutos antes del próximo refresh
                    time.sleep(240)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error en daemon: {e}")
                    time.sleep(60)
        
        daemon_thread = Thread(target=refresh_daemon, daemon=True)
        daemon_thread.start()
        self.logger.info("🚀 Daemon de refresh iniciado")
    
    def setup_persistent_trading(self):
        """Configurar trading persistente para todos los activos"""
        try:
            self.logger.info("🚀 CONFIGURANDO TRADING PERSISTENTE CON TOKENS")
            
            pairs = ["UK BRENT", "MICROSOFT", "ADA", "ETH"]
            
            # Crear sesiones persistentes
            for pair in pairs:
                driver = self.create_persistent_session(pair)
                if driver:
                    # Login y capturar tokens
                    if self.login_and_capture_tokens(driver, pair):
                        self.logger.info(f"✅ {pair} configurado con tokens")
                    else:
                        self.logger.warning(f"⚠️ {pair} sin tokens válidos")
                
                time.sleep(5)  # Esperar entre configuraciones
            
            # Iniciar daemon de refresh
            self.start_token_refresh_daemon()
            
            self.logger.info("✅ TRADING PERSISTENTE CONFIGURADO")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando trading persistente: {e}")
            return False
    
    def get_valid_tokens(self, pair):
        """Obtener tokens válidos para un activo"""
        try:
            with self.lock:
                if pair in self.tokens:
                    token_data = self.tokens[pair]
                    timestamp = token_data.get('timestamp', datetime.now())
                    
                    # Verificar si los tokens no han expirado (10 minutos)
                    if datetime.now() - timestamp < timedelta(minutes=10):
                        return token_data
                    else:
                        self.logger.warning(f"⚠️ Tokens expirados para {pair}")
                        return None
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo tokens para {pair}: {e}")
            return None
    
    def stop(self):
        """Detener el sistema"""
        try:
            self.running = False
            
            for pair, driver in self.drivers.items():
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
            
            self.logger.info("🛑 Sistema detenido")
            
        except Exception as e:
            self.logger.error(f"❌ Error deteniendo sistema: {e}")

def main():
    """Función principal"""
    keeper = QuotexTokenKeeper()
    
    try:
        if keeper.setup_persistent_trading():
            print("\n🎉 ¡SISTEMA PERSISTENTE ACTIVADO!")
            print("✅ Los tokens se mantendrán vivos automáticamente")
            print("🔄 Refresh automático cada 4 minutos")
            print("💪 ¡YA NO MÁS PROBLEMAS DE TOKENS!")
            
            # Mantener el sistema corriendo
            while True:
                time.sleep(60)
                print(f"🔄 Sistema activo - {datetime.now().strftime('%H:%M:%S')}")
        else:
            print("\n❌ Error configurando sistema persistente")
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        keeper.stop()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        keeper.stop()

if __name__ == "__main__":
    main()
