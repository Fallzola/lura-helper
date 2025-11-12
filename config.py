"""
Configurações do Bot Plurall
"""
import os
from pathlib import Path

class Config:
    """Classe de configuração do bot"""

    # Diretórios
    BASE_DIR = Path(__file__).parent
    LINKS_FILE = BASE_DIR / "links_de_exercicios.txt"

    # Timeouts (em segundos)
    LOGIN_TIMEOUT = 300  # 5 minutos para fazer login
    PAGE_LOAD_TIMEOUT = 15
    ELEMENT_WAIT_TIMEOUT = 10
    MINIMAL_LOAD_TIMEOUT = 3

    # Tentativas - AJUSTADO para evitar chutes rápidos sem carregamento
    MAX_RETRIES = 3  # Reduzido de 5 para 3 tentativas
    RETRY_DELAY = 2  # Aumentado de 1 para 2 segundos entre tentativas
    WAIT_AFTER_CLICK = 3  # Tempo de espera após clicar em uma opção

    # Configurações de respostas
    MIN_DOTS = 20  # Mínimo de pontos para questões de texto
    MAX_DOTS = 40  # Máximo de pontos para questões de texto

    # URLs
    LOGIN_URL = "https://login.plurall.net/"
    API_BASE_URL = "https://api.plurall.net/api"
    ATIVIDADES_URL = "https://atividades.plurall.net"

    # Chrome Options - Otimizações de velocidade
    CHROME_ARGUMENTS = [
        "--start-maximized",
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",
        "--disable-javascript-harmony-shipping",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection"
    ]

    # Seletores CSS
    class Selectors:
        """Seletores CSS para elementos da página"""
        # Questões de múltipla escolha
        OPTION_LIST = "li.option"
        OPTION_SPAN = "li.option span[data-test-id='option']"
        ICON_CHECK = '[data-test-id="icon-Check"]'
        ICON_CANCEL = '[data-test-id="icon-Cancel"]'

        # Questões de texto
        TEXTAREA = '[data-test-id="response-textarea"]'
        SEND_BUTTON = 'button[type="button"][data-test-id="send-button"]'
        CONFIRM_BUTTON = 'button[type="button"][class*="css-sakhm0"]'
        ANSWER_CONTAINER = '.Answer-module_answer-container__HR7MK.answer-container'

        # Questões de imagem
        IMAGE_BUTTON = '[data-test-id="input-image-id-button"]'

        # Containers de resposta
        ANSWER_CONTAINERS = [
            '.Answer-module_answer-container__HR7MK.answer-container',
            '[class*="Answer-module_answer-container"]',
            '[class*="answer-container"]',
            '[class*="answer"][class*="container"]'
        ]

    @classmethod
    def get_links_file(cls, apostila: str = None) -> Path:
        """
        Retorna o caminho do arquivo de links

        Args:
            apostila: Nome da apostila (ex: "apostila3")

        Returns:
            Path do arquivo de links
        """
        if apostila:
            return cls.BASE_DIR / apostila / "links_de_exercicios.txt"
        return cls.LINKS_FILE

    @classmethod
    def validate_config(cls):
        """Valida as configurações"""
        if not cls.LINKS_FILE.exists():
            raise FileNotFoundError(f"Arquivo de links não encontrado: {cls.LINKS_FILE}")
