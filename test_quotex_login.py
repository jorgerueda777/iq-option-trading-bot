#!/usr/bin/env python3
"""
Test de Login Automático en Quotex - Estilo API Test
Prueba diferentes métodos de login automático sin intervención manual
"""

import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

class QuotexLoginTester:
    def __init__(self):
        self.driver = None
        self.login_methods = []
        
        # Credenciales
        self.email = "arnolbrom634@gmail.com"
        self.password = "7decadames"
    
    def setup_chrome(self):
        """Configurar Chrome optimizado para login"""
        try:
            logging.info("🛡️ Configurando Chrome para login automático...")
            
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            
            # User agent realista
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.125 Safari/537.36")
            
            self.driver = uc.Chrome(options=options, version_main=141)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.maximize_window()
            
            logging.info("✅ Chrome configurado para login")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error configurando Chrome: {e}")
            return False
    
    def test_direct_login_page(self):
        """Probar login directo en página de login"""
        try:
            logging.info("🧪 PROBANDO LOGIN DIRECTO...")
            
            # Ir a página de login
            login_urls = [
                "https://qxbroker.com/login",
                "https://qxbroker.com/auth/login",
                "https://qxbroker.com/sign-in",
                "https://qxbroker.com/"
            ]
            
            for url in login_urls:
                try:
                    logging.info(f"🔍 Probando URL: {url}")
                    self.driver.get(url)
                    time.sleep(5)
                    
                    # Buscar formulario de login
                    login_found = self.find_and_fill_login_form()
                    if login_found:
                        logging.info(f"✅ Login encontrado en: {url}")
                        return True
                    else:
                        logging.info(f"❌ No se encontró login en: {url}")
                        
                except Exception as e:
                    logging.info(f"❌ Error en {url}: {str(e)[:50]}")
                    continue
            
            return False
            
        except Exception as e:
            logging.error(f"❌ Error en login directo: {e}")
            return False
    
    def find_and_fill_login_form(self):
        """Buscar y llenar formulario de login"""
        try:
            # Selectores para campos de email
            email_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input[name='username']",
                "input[name='login']",
                "input[placeholder*='email']",
                "input[placeholder*='Email']",
                "input[placeholder*='correo']",
                "#email",
                "#username",
                "#login",
                ".email-input",
                ".login-input"
            ]
            
            # Selectores para campos de password
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[name='pass']",
                "input[placeholder*='password']",
                "input[placeholder*='Password']",
                "input[placeholder*='contraseña']",
                "#password",
                "#pass",
                ".password-input"
            ]
            
            # Selectores para botones de login
            login_button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Login')",
                "button:contains('Sign in')",
                "button:contains('Entrar')",
                "button:contains('Iniciar')",
                ".login-button",
                ".submit-button",
                "#login-btn",
                "#submit"
            ]
            
            email_field = None
            password_field = None
            login_button = None
            
            # Buscar campo de email
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logging.info(f"📧 Email encontrado: {selector}")
                    break
                except:
                    continue
            
            # Buscar campo de password
            for selector in password_selectors:
                try:
                    password_field = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logging.info(f"🔑 Password encontrado: {selector}")
                    break
                except:
                    continue
            
            # Buscar botón de login
            for selector in login_button_selectors:
                try:
                    login_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logging.info(f"🔘 Botón encontrado: {selector}")
                    break
                except:
                    continue
            
            # Si encontramos los campos, llenar y enviar
            if email_field and password_field:
                logging.info("📝 Llenando formulario de login...")
                
                # Llenar email
                email_field.clear()
                email_field.send_keys(self.email)
                time.sleep(1)
                
                # Llenar password
                password_field.clear()
                password_field.send_keys(self.password)
                time.sleep(1)
                
                # Hacer clic en login o presionar Enter
                if login_button:
                    login_button.click()
                    logging.info("🔘 Botón de login clickeado")
                else:
                    password_field.send_keys(Keys.RETURN)
                    logging.info("⌨️ Enter presionado en password")
                
                # Esperar respuesta
                time.sleep(5)
                
                # Verificar si el login fue exitoso
                return self.verify_login_success()
            
            else:
                logging.info("❌ No se encontraron campos de login")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error llenando formulario: {e}")
            return False
    
    def verify_login_success(self):
        """Verificar si el login fue exitoso"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title.lower()
            
            # Indicadores de login exitoso
            success_indicators = [
                "dashboard" in current_url,
                "trade" in current_url,
                "trading" in current_url,
                "account" in current_url,
                "profile" in current_url,
                "dashboard" in page_title,
                "trading" in page_title,
                "quotex" in page_title and "login" not in page_title
            ]
            
            # Indicadores de login fallido
            error_indicators = [
                "login" in current_url,
                "error" in current_url,
                "invalid" in page_title,
                "incorrect" in page_title
            ]
            
            # Buscar elementos que indiquen login exitoso
            try:
                success_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".user-menu, .account-info, .balance, .trading-panel, .dashboard")
                if success_elements:
                    success_indicators.append(True)
            except:
                pass
            
            # Buscar mensajes de error
            try:
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".error, .alert-danger, .login-error, .invalid")
                if error_elements:
                    error_indicators.append(True)
            except:
                pass
            
            if any(success_indicators) and not any(error_indicators):
                logging.info("✅ Login exitoso detectado")
                logging.info(f"   URL: {current_url}")
                logging.info(f"   Título: {page_title}")
                return True
            else:
                logging.info("❌ Login falló")
                logging.info(f"   URL: {current_url}")
                logging.info(f"   Título: {page_title}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error verificando login: {e}")
            return False
    
    def test_google_login(self):
        """Probar login con Google"""
        try:
            logging.info("🧪 PROBANDO LOGIN CON GOOGLE...")
            
            # Buscar botón de Google
            google_selectors = [
                "button:contains('Google')",
                "a:contains('Google')",
                ".google-login",
                ".social-google",
                "#google-login",
                "button[data-provider='google']"
            ]
            
            for selector in google_selectors:
                try:
                    google_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    logging.info(f"🔍 Botón Google encontrado: {selector}")
                    google_button.click()
                    time.sleep(3)
                    
                    # Aquí se abriría popup de Google
                    # Por ahora solo detectamos si se abre
                    if "google" in self.driver.current_url or len(self.driver.window_handles) > 1:
                        logging.info("✅ Popup de Google detectado")
                        return True
                    
                except:
                    continue
            
            logging.info("❌ No se encontró botón de Google")
            return False
            
        except Exception as e:
            logging.error(f"❌ Error en login Google: {e}")
            return False
    
    def test_social_logins(self):
        """Probar otros logins sociales"""
        try:
            logging.info("🧪 PROBANDO LOGINS SOCIALES...")
            
            social_providers = [
                ("Facebook", ["facebook", "fb"]),
                ("Twitter", ["twitter"]),
                ("Apple", ["apple"]),
                ("Telegram", ["telegram"])
            ]
            
            found_providers = []
            
            for provider, keywords in social_providers:
                for keyword in keywords:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, 
                            f"button:contains('{keyword}'), a:contains('{keyword}'), .{keyword}-login")
                        
                        if elements:
                            found_providers.append(provider)
                            logging.info(f"✅ {provider} login disponible")
                            break
                    except:
                        continue
            
            if found_providers:
                logging.info(f"📱 Proveedores sociales: {', '.join(found_providers)}")
                return True
            else:
                logging.info("❌ No se encontraron logins sociales")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error en logins sociales: {e}")
            return False
    
    def run_full_login_test(self):
        """Ejecutar prueba completa de login"""
        try:
            logging.info("🚀 INICIANDO PRUEBA COMPLETA DE LOGIN AUTOMÁTICO")
            logging.info("=" * 60)
            
            # 1. Configurar Chrome
            if not self.setup_chrome():
                return False
            
            # 2. Probar login directo
            direct_login = self.test_direct_login_page()
            
            # 3. Si el login directo falló, probar otros métodos
            if not direct_login:
                logging.info("🔄 Probando métodos alternativos...")
                
                # Volver a página principal
                self.driver.get("https://qxbroker.com/")
                time.sleep(3)
                
                # Probar Google login
                google_login = self.test_google_login()
                
                # Probar otros logins sociales
                social_logins = self.test_social_logins()
            
            # 4. Resumen final
            logging.info("🎯 RESUMEN DE PRUEBAS DE LOGIN:")
            logging.info("=" * 60)
            
            if direct_login:
                logging.info("✅ Login directo: EXITOSO")
            else:
                logging.info("❌ Login directo: FALLÓ")
            
            # Mantener ventana abierta para inspección
            if direct_login:
                logging.info("🔍 LOGIN EXITOSO - VENTANA ABIERTA PARA INSPECCIÓN")
                logging.info("   Presiona ENTER para cerrar...")
                input()
            else:
                logging.info("❌ LOGIN FALLÓ - Cerrando en 10 segundos...")
                time.sleep(10)
            
            return direct_login
            
        except Exception as e:
            logging.error(f"❌ Error en prueba de login: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Función principal"""
    tester = QuotexLoginTester()
    success = tester.run_full_login_test()
    
    if success:
        logging.info("🎉 PRUEBA DE LOGIN EXITOSA")
    else:
        logging.info("💥 PRUEBA DE LOGIN FALLÓ")

if __name__ == "__main__":
    main()
