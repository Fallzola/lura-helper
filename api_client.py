"""
Cliente para interação com a API do Plurall
"""
import re
import random
import requests
from typing import Dict, Optional

from config import Config
from logger import logger, log_api
from exceptions import APIException, AuthenticationException


class PluralAPIClient:
    """Cliente para interagir com a API do Plurall"""

    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.driver = driver_manager.driver
        self.token = None
        self.client_id = None

    def extract_ids_from_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extrai os IDs necessários da URL do exercício

        Args:
            url: URL do exercício

        Returns:
            Dicionário com os IDs ou None
        """
        pattern = r'/material/(\d+)/aula/(\d+)/tarefa/(\d+)/exercicio/(\d+)/'
        match = re.search(pattern, url)

        if match:
            return {
                'material_id': match.group(1),
                'aula_id': match.group(2),
                'tarefa_id': match.group(3),
                'exercicio_id': match.group(4)
            }
        return None

    def get_auth_token(self) -> Optional[str]:
        """
        Extrai o token de autorização do navegador

        Returns:
            Token de autorização ou None
        """
        try:
            # Método 1: Procura por tokens no HTML
            page_source = self.driver_manager.get_page_source()

            if "Bearer" in page_source:
                match = re.search(r'Bearer\s+([a-f0-9]{32})', page_source)
                if match:
                    self.token = match.group(1)
                    logger.info(f"🔑 Token encontrado no HTML: {self.token[:8]}...")
                    return self.token

            # Método 2: Procura tokens sem "Bearer"
            matches = re.findall(r'[a-f0-9]{32}', page_source)
            for match in matches:
                if len(match) == 32 and all(c in '0123456789abcdef' for c in match):
                    self.token = match
                    logger.info(f"🔑 Token encontrado: {self.token[:8]}...")
                    return self.token

            # Método 3: Tenta extrair do localStorage
            token = self.driver_manager.execute_script("""
                return localStorage.getItem('auth_token') ||
                       sessionStorage.getItem('auth_token') ||
                       localStorage.getItem('token') ||
                       sessionStorage.getItem('token');
            """)
            if token:
                self.token = token
                logger.info(f"🔑 Token encontrado no storage: {self.token[:8]}...")
                return self.token

            # Método 4: Tenta extrair dos cookies
            cookies = self.driver_manager.get_cookies()
            for cookie in cookies:
                if 'auth' in cookie['name'].lower() or 'token' in cookie['name'].lower():
                    self.token = cookie['value']
                    logger.info(f"🔑 Token encontrado nos cookies: {self.token[:8]}...")
                    return self.token

            # Método 5: Procura por variáveis JavaScript
            js_vars = self.driver_manager.execute_script("""
                return {
                    'auth_token': window.auth_token || window.token || window.AUTH_TOKEN || window.TOKEN,
                    'user_token': window.user_token || window.userToken || window.USER_TOKEN,
                    'session_token': window.session_token || window.sessionToken || window.SESSION_TOKEN
                };
            """)

            for key, value in js_vars.items():
                if value and len(str(value)) >= 20:
                    self.token = str(value)
                    logger.info(f"🔑 Token encontrado em variável JS {key}: {self.token[:8]}...")
                    return self.token

        except Exception as e:
            logger.warning(f"Erro ao extrair token: {str(e)}")

        logger.error("Token não encontrado por nenhum método")
        return None

    def get_client_id(self) -> Optional[str]:
        """
        Extrai o client ID do navegador

        Returns:
            Client ID ou None
        """
        try:
            # Método 1: Procura no HTML
            page_source = self.driver_manager.get_page_source()

            if "PLTR." in page_source:
                match = re.search(r'PLTR\.[a-f0-9-]+\.\d+', page_source)
                if match:
                    self.client_id = match.group(0)
                    logger.info(f"🆔 Client ID encontrado: {self.client_id}")
                    return self.client_id

            # Método 2: Procura em elementos específicos
            elements = self.driver_manager.find_elements(
                By.CSS_SELECTOR,
                "[data-client-id], [client-id], .client-id"
            )
            for element in elements:
                client_id = (
                    element.get_attribute("data-client-id") or
                    element.get_attribute("client-id") or
                    element.text
                )
                if client_id and "PLTR." in client_id:
                    self.client_id = client_id
                    return self.client_id

            # Método 3: Gera um client ID baseado no padrão
            logger.warning("Client ID não encontrado, gerando um baseado no padrão...")
            import time
            timestamp = int(time.time() * 1000)
            random_hex = ''.join(random.choices('0123456789abcdef', k=32))
            self.client_id = f"PLTR.{random_hex}.{timestamp}"
            logger.info(f"🆔 Client ID gerado: {self.client_id}")
            return self.client_id

        except Exception as e:
            logger.warning(f"Erro ao extrair client ID: {str(e)}")
            # Fallback: gera um client ID
            import time
            timestamp = int(time.time() * 1000)
            random_hex = ''.join(random.choices('0123456789abcdef', k=32))
            self.client_id = f"PLTR.{random_hex}.{timestamp}"
            logger.info(f"🆔 Client ID gerado como fallback: {self.client_id}")
            return self.client_id

    def answer_via_api(self, url: str) -> bool:
        """
        Responde uma questão usando a API do Plurall

        Args:
            url: URL do exercício

        Returns:
            True se respondeu com sucesso, False caso contrário
        """
        try:
            # Extrai IDs da URL
            ids = self.extract_ids_from_url(url)
            if not ids:
                logger.error("Não foi possível extrair IDs da URL")
                return False

            tarefa_id = ids['tarefa_id']
            exercicio_id = ids['exercicio_id']

            # Obtém token e client ID
            if not self.token:
                self.token = self.get_auth_token()
            if not self.client_id:
                self.client_id = self.get_client_id()

            if not self.token or not self.client_id:
                logger.error("Não foi possível obter credenciais de autenticação")
                raise AuthenticationException("Falha ao obter credenciais")

            # Headers necessários
            headers = {
                'authority': 'api.plurall.net',
                'accept': 'application/json, text/plain, */*, vnd.plurall.api.v3+json',
                'accept-language': 'pt-BR,pt;q=0.9',
                'authorization': f'Bearer {self.token}',
                'client': self.client_id,
                'content-type': 'application/json',
                'origin': Config.ATIVIDADES_URL,
                'referer': f'{Config.ATIVIDADES_URL}/',
                'sec-ch-ua': '"Not;A=Brand";v="99", "Brave";v="139", "Chromium";v="139"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Detecta número de opções na página
            from selenium.webdriver.common.by import By
            options_elements = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_LIST)
            num_options = len(options_elements)

            # Ajusta opções baseado no número real
            if num_options == 4:
                options = ['a', 'b', 'c', 'd']
                logger.info(f"📊 Questão com {num_options} opções (A, B, C, D)")
            elif num_options == 3:
                options = ['a', 'b', 'c']
                logger.info(f"📊 Questão com {num_options} opções (A, B, C)")
            elif num_options == 2:
                options = ['a', 'b']
                logger.info(f"📊 Questão com {num_options} opções (A, B)")
            else:
                options = ['a', 'b', 'c', 'd', 'e']
                logger.info(f"📊 Questão com {num_options} opções")

            # Tenta cada opção
            for option in options:
                logger.info(f"🎲 Tentando opção: {option.upper()}")

                # Payload
                payload = {"answer": option}

                # URL da API
                api_url = f"{Config.API_BASE_URL}/task_workflows/{tarefa_id}/subtasks/{exercicio_id}/answer"

                # Faz request POST
                response = requests.post(api_url, headers=headers, json=payload)

                if response.status_code == 200:
                    data = response.json()

                    if data.get('result') == 'success':
                        status = data['data']['update_interface_data']['status']
                        user_answer = data['data']['update_interface_data']['user_answer']
                        attempts = data['data']['update_interface_data']['attempts_in_words']

                        log_api(f"Resposta enviada: {user_answer.upper()}")
                        log_api(f"Status: {status}")
                        log_api(f"{attempts}")

                        if status == 'correct':
                            logger.info("🎉 Questão respondida corretamente via API!")
                            return True
                        elif status in ['completed', 'finished']:
                            logger.info("✅ Questão marcada como completa/finalizada!")
                            return True
                        elif status == 'wrong':
                            logger.info("❌ Opção incorreta, tentando próxima...")
                            continue
                        else:
                            logger.warning(f"Status desconhecido: {status}")
                            if any(keyword in str(data).lower() for keyword in ['completed', 'finished', 'success']):
                                logger.info("✅ Indicadores de sucesso encontrados!")
                                return True
                            continue
                    else:
                        logger.error(f"Erro na resposta da API: {data}")
                        continue
                else:
                    logger.error(f"Erro HTTP: {response.status_code}")
                    continue

            logger.warning("Todas as opções foram testadas sem sucesso")
            return False

        except Exception as e:
            logger.error(f"Erro ao responder via API: {str(e)}")
            raise APIException(f"Falha na API: {str(e)}")

    def debug_authentication(self) -> bool:
        """Debug de informações de autenticação"""
        logger.info("🔍 Debug: Procurando informações de autenticação...")

        try:
            # Verifica se está na página de login
            if "login" in self.driver_manager.current_url.lower():
                logger.warning("Ainda na página de login. Faça login primeiro!")
                return False

            page_source = self.driver_manager.get_page_source()

            # Procura tokens Bearer
            bearer_tokens = re.findall(r'Bearer\s+([a-f0-9]{32})', page_source)
            if bearer_tokens:
                logger.info(f"🔑 Tokens Bearer encontrados: {len(bearer_tokens)}")
                for i, token in enumerate(bearer_tokens[:3]):
                    logger.info(f"   {i+1}. {token[:8]}...")

            # Procura client IDs
            client_ids = re.findall(r'PLTR\.[a-f0-9-]+\.\d+', page_source)
            if client_ids:
                logger.info(f"🆔 Client IDs encontrados: {len(client_ids)}")
                for i, client_id in enumerate(client_ids[:3]):
                    logger.info(f"   {i+1}. {client_id}")

            # Verifica storage
            storage_data = self.driver_manager.execute_script("""
                return {
                    'localStorage': Object.keys(localStorage).filter(key =>
                        key.toLowerCase().includes('token') ||
                        key.toLowerCase().includes('auth') ||
                        key.toLowerCase().includes('client')
                    ),
                    'sessionStorage': Object.keys(sessionStorage).filter(key =>
                        key.toLowerCase().includes('token') ||
                        key.toLowerCase().includes('auth') ||
                        key.toLowerCase().includes('client')
                    )
                };
            """)

            if storage_data['localStorage']:
                logger.info(f"💾 Chaves no localStorage: {storage_data['localStorage']}")
            if storage_data['sessionStorage']:
                logger.info(f"💾 Chaves no sessionStorage: {storage_data['sessionStorage']}")

            # Verifica cookies
            cookies = self.driver_manager.get_cookies()
            auth_cookies = [c for c in cookies if 'auth' in c['name'].lower() or 'token' in c['name'].lower()]
            if auth_cookies:
                logger.info(f"🍪 Cookies de autenticação: {len(auth_cookies)}")
                for cookie in auth_cookies[:3]:
                    logger.info(f"   {cookie['name']}: {cookie['value'][:20]}...")

            return True

        except Exception as e:
            logger.error(f"Erro no debug: {str(e)}")
            return False
