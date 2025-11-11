"""
Gerenciador do WebDriver
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import Config
from logger import logger, log_success, log_loading
from exceptions import WebDriverException, LoginException


class WebDriverManager:
    """Gerencia o WebDriver do Selenium"""

    def __init__(self):
        self.driver = None
        self.wait = None

    def initialize_driver(self):
        """Inicializa o Chrome WebDriver com configurações otimizadas"""
        try:
            log_loading("Inicializando Chrome...")

            # Configurar opções do Chrome
            chrome_options = Options()
            for arg in Config.CHROME_ARGUMENTS:
                chrome_options.add_argument(arg)

            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Inicializar driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, Config.ELEMENT_WAIT_TIMEOUT)

            # Remover propriedade webdriver para evitar detecção
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            log_success("Chrome inicializado com sucesso!")
            return self.driver

        except Exception as e:
            logger.error(f"Erro ao inicializar Chrome: {str(e)}")
            logger.info("\n💡 SOLUÇÕES:")
            logger.info("   1. Certifique-se de que o Google Chrome está instalado")
            logger.info("   2. Baixe o ChromeDriver manualmente de: https://chromedriver.chromium.org/")
            logger.info("   3. Coloque o ChromeDriver na mesma pasta do script ou no PATH do sistema")
            logger.info("   4. Ou execute: pip install --upgrade selenium")
            raise WebDriverException(f"Falha ao inicializar WebDriver: {str(e)}")

    def wait_for_login(self):
        """Aguarda o usuário fazer login"""
        try:
            log_loading("Abrindo Plurall...")
            self.driver.get(Config.LOGIN_URL)

            log_loading("Aguardando login do usuário...")
            wait = WebDriverWait(self.driver, Config.LOGIN_TIMEOUT)

            # Aguardar até que a URL mude (indicando login bem-sucedido)
            wait.until(lambda d: "login.plurall.net" not in d.current_url)

            log_success("Login detectado! Usuário logado com sucesso.")
            return True

        except Exception as e:
            logger.error(f"Erro durante login: {str(e)}")
            raise LoginException(f"Falha no processo de login: {str(e)}")

    def navigate_to(self, url: str):
        """Navega para uma URL"""
        try:
            self.driver.get(url)
        except Exception as e:
            logger.error(f"Erro ao navegar para {url}: {str(e)}")
            raise WebDriverException(f"Falha ao navegar: {str(e)}")

    def refresh(self):
        """Atualiza a página"""
        try:
            self.driver.refresh()
        except Exception as e:
            logger.error(f"Erro ao atualizar página: {str(e)}")

    def find_element(self, by: By, selector: str, timeout: int = None):
        """Encontra um elemento na página"""
        try:
            if timeout:
                wait = WebDriverWait(self.driver, timeout)
                return wait.until(EC.presence_of_element_located((by, selector)))
            return self.driver.find_element(by, selector)
        except Exception:
            return None

    def find_elements(self, by: By, selector: str):
        """Encontra múltiplos elementos na página"""
        try:
            return self.driver.find_elements(by, selector)
        except Exception:
            return []

    def wait_for_element(self, by: By, selector: str, timeout: int = None):
        """Aguarda um elemento aparecer"""
        try:
            wait_time = timeout or Config.ELEMENT_WAIT_TIMEOUT
            wait = WebDriverWait(self.driver, wait_time)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except Exception:
            return None

    def wait_for_page_load(self):
        """Aguarda a página carregar completamente"""
        try:
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        except Exception as e:
            logger.warning(f"Timeout aguardando carregamento da página: {str(e)}")

    def get_page_source(self):
        """Retorna o código fonte da página"""
        return self.driver.page_source

    def execute_script(self, script: str, *args):
        """Executa JavaScript"""
        return self.driver.execute_script(script, *args)

    def get_cookies(self):
        """Retorna os cookies"""
        return self.driver.get_cookies()

    @property
    def current_url(self):
        """Retorna a URL atual"""
        return self.driver.current_url

    def quit(self):
        """Fecha o navegador"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("👋 Navegador fechado!")
            except Exception as e:
                logger.error(f"Erro ao fechar navegador: {str(e)}")

    def __enter__(self):
        """Context manager entry"""
        self.initialize_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.quit()
