"""
Exceções customizadas do Bot Plurall
"""


class PluralBotException(Exception):
    """Exceção base para o bot"""
    pass


class LoginException(PluralBotException):
    """Exceção para erros de login"""
    pass


class QuestionNotFoundException(PluralBotException):
    """Exceção quando questão não é encontrada"""
    pass


class QuestionTypeUnknownException(PluralBotException):
    """Exceção quando tipo de questão não é reconhecido"""
    pass


class AuthenticationException(PluralBotException):
    """Exceção para erros de autenticação"""
    pass


class APIException(PluralBotException):
    """Exceção para erros na API"""
    pass


class WebDriverException(PluralBotException):
    """Exceção para erros do WebDriver"""
    pass


class ConfigException(PluralBotException):
    """Exceção para erros de configuração"""
    pass
