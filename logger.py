"""
Sistema de logging do Bot Plurall
"""
import logging
import sys
from datetime import datetime
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Formatter customizado com cores para console"""

    # Códigos de cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Ciano
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarelo
        'ERROR': '\033[31m',      # Vermelho
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    # Emojis para cada nível
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }

    def format(self, record):
        # Adiciona cor ao level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.EMOJIS.get(levelname, '')} {levelname}"

        # Formata a mensagem
        result = super().format(record)

        return result


class Logger:
    """Classe gerenciadora de logging"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """Configura o logger"""
        # Cria logger
        self._logger = logging.getLogger('PluralBot')
        self._logger.setLevel(logging.DEBUG)

        # Remove handlers existentes
        self._logger.handlers.clear()

        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        # Handler para arquivo
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f'plurall_bot_{datetime.now():%Y%m%d_%H%M%S}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Adiciona handlers
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)

    @property
    def logger(self):
        """Retorna o logger configurado"""
        return self._logger


# Instância global do logger
_logger_instance = Logger()
logger = _logger_instance.logger


# Funções de conveniência
def debug(msg, *args, **kwargs):
    """Log debug"""
    logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Log info"""
    logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Log warning"""
    logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Log error"""
    logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Log critical"""
    logger.critical(msg, *args, **kwargs)


# Funções com emojis específicos (mantendo compatibilidade com código antigo)
def log_start(msg):
    """Log de início com emoji de foguete"""
    info(f"🚀 {msg}")


def log_success(msg):
    """Log de sucesso com emoji de check"""
    info(f"✅ {msg}")


def log_progress(msg):
    """Log de progresso"""
    info(f"📝 {msg}")


def log_timer(msg):
    """Log de timer"""
    info(f"⏱️  {msg}")


def log_link(msg):
    """Log de link"""
    info(f"🔗 {msg}")


def log_loading(msg):
    """Log de carregamento"""
    info(f"⏳ {msg}")


def log_fast(msg):
    """Log de ação rápida"""
    info(f"⚡ {msg}")


def log_retry(msg):
    """Log de retry"""
    warning(f"🔄 {msg}")


def log_api(msg):
    """Log de API"""
    info(f"📡 {msg}")


def log_click(msg):
    """Log de clique"""
    info(f"👆 {msg}")


def log_question(msg):
    """Log de questão"""
    info(f"❓ {msg}")


def log_image(msg):
    """Log de imagem"""
    info(f"🖼️  {msg}")


def log_celebration(msg):
    """Log de celebração"""
    info(f"🎉 {msg}")
