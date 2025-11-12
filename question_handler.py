"""
Gerenciador de questões do Plurall
"""
import time
import random
from enum import Enum
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import Config
from logger import (logger, log_progress, log_success, log_loading, log_fast,
                   log_retry, log_click, log_celebration, log_image)
from exceptions import QuestionNotFoundException, QuestionTypeUnknownException


class QuestionType(Enum):
    """Tipos de questões"""
    MULTIPLE_CHOICE = "multipla_escolha"
    MULTIPLE_CHOICE_ANSWERED = "multipla_escolha_respondida"
    TEXT = "texto"
    TEXT_ANSWERED = "texto_respondida"
    IMAGE = "imagem"
    UNKNOWN = "desconhecido"


class QuestionHandler:
    """Gerencia o processamento de questões"""

    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.driver = driver_manager.driver

    def detect_question_type(self, max_attempts: int = None) -> QuestionType:
        """
        Detecta o tipo de questão atual com melhor espera de carregamento

        Args:
            max_attempts: Número máximo de tentativas

        Returns:
            QuestionType identificado
        """
        max_attempts = max_attempts or Config.MAX_RETRIES
        attempt = 0

        while attempt < max_attempts:
            attempt += 1

            try:
                # Verifica questão de texto já respondida (alta prioridade)
                for selector in Config.Selectors.ANSWER_CONTAINERS:
                    if self.driver_manager.find_element(By.CSS_SELECTOR, selector):
                        logger.info("✅ Questão de texto detectada: já respondida")
                        return QuestionType.TEXT_ANSWERED

                # Verifica questão de texto não respondida
                if self.driver_manager.find_element(By.CSS_SELECTOR, Config.Selectors.TEXTAREA):
                    logger.info("✅ Questão de texto detectada: aguardando resposta")
                    return QuestionType.TEXT

                # Verifica questão de múltipla escolha
                options = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_LIST)
                if len(options) >= 2:
                    # Verifica se já foi respondida
                    for option in options:
                        try:
                            check = option.find_element(By.XPATH, f'.//*[@data-test-id="icon-Check"]')
                            if check:
                                logger.info("✅ Questão múltipla escolha detectada: já respondida")
                                return QuestionType.MULTIPLE_CHOICE_ANSWERED
                        except:
                            continue
                    logger.info(f"✅ Questão múltipla escolha detectada: {len(options)} opções")
                    return QuestionType.MULTIPLE_CHOICE

                # Verifica questão de imagem
                if self.driver_manager.find_element(By.CSS_SELECTOR, Config.Selectors.IMAGE_BUTTON):
                    logger.info("✅ Questão de imagem detectada")
                    return QuestionType.IMAGE

                # Se não detectou nada, aguarda mais tempo antes de tentar novamente
                if attempt < max_attempts:
                    wait_time = Config.RETRY_DELAY * attempt  # Espera progressiva
                    log_retry(f"Tentativa {attempt}/{max_attempts} falhou, aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                logger.warning("❌ Tipo de questão não identificado após todas as tentativas")
                return QuestionType.UNKNOWN

            except Exception as e:
                logger.warning(f"Erro na detecção (tentativa {attempt}): {str(e)}")
                if attempt < max_attempts:
                    wait_time = Config.RETRY_DELAY * attempt  # Espera progressiva
                    time.sleep(wait_time)
                    continue
                return QuestionType.UNKNOWN

    def wait_minimal_load(self) -> QuestionType:
        """Aguarda carregamento mínimo da página"""
        log_fast("Aguardando carregamento mínimo...")

        try:
            wait = WebDriverWait(self.driver, Config.MINIMAL_LOAD_TIMEOUT)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(1)
            return self.detect_question_type()
        except Exception as e:
            logger.warning(f"Erro no carregamento mínimo: {str(e)}")
            return QuestionType.UNKNOWN

    def wait_complete_load(self):
        """Aguarda carregamento completo da página"""
        log_loading("Aguardando carregamento completo...")

        try:
            wait = WebDriverWait(self.driver, Config.PAGE_LOAD_TIMEOUT)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(2)

            # Aguarda pelo menos um elemento principal
            main_elements = [
                Config.Selectors.OPTION_LIST,
                Config.Selectors.TEXTAREA,
                Config.Selectors.IMAGE_BUTTON,
                Config.Selectors.ANSWER_CONTAINER
            ]

            for selector in main_elements:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    log_success(f"Elemento encontrado: {selector}")
                    break
                except:
                    continue

            log_success("Página carregada completamente!")

        except Exception as e:
            logger.warning(f"Erro no carregamento completo: {str(e)}")

    def answer_text_question(self) -> bool:
        """Responde uma questão de texto"""
        log_progress("Bot respondendo questão de texto...")

        try:
            # Encontra textarea
            textarea = self.driver_manager.find_element(By.CSS_SELECTOR, Config.Selectors.TEXTAREA)
            if not textarea:
                logger.error("Textarea não encontrada")
                return False

            # Gera resposta aleatória
            num_dots = random.randint(Config.MIN_DOTS, Config.MAX_DOTS)
            answer = "." * num_dots

            logger.info(f"✍️  Escrevendo resposta: {num_dots} pontos")

            # Escreve resposta
            textarea.clear()
            textarea.send_keys(answer)

            # Clica em enviar
            send_button = self.driver_manager.find_element(By.CSS_SELECTOR, Config.Selectors.SEND_BUTTON)
            if not send_button:
                logger.error("Botão de enviar não encontrado")
                return False

            logger.info("📤 Enviando resposta...")
            send_button.click()

            # Aguarda e clica em confirmar
            wait = WebDriverWait(self.driver, 5)
            try:
                confirm_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, Config.Selectors.CONFIRM_BUTTON))
                )
                log_success("Popup de confirmação encontrado, confirmando envio...")
                confirm_button.click()
            except:
                logger.warning("Popup de confirmação não encontrado, tentando continuar...")

            # Aguarda resposta ser processada
            wait = WebDriverWait(self.driver, 10)
            try:
                wait.until(lambda d:
                    len(d.find_elements(By.CSS_SELECTOR, Config.Selectors.TEXTAREA)) == 0 or
                    len(d.find_elements(By.CSS_SELECTOR, Config.Selectors.ANSWER_CONTAINER)) > 0
                )
                log_success("Questão de texto respondida com sucesso!")
                return True
            except:
                logger.warning("Timeout aguardando confirmação, mas assumindo sucesso")
                return True

        except Exception as e:
            logger.error(f"Erro ao responder questão de texto: {str(e)}")
            return False

    def answer_multiple_choice_question(self) -> bool:
        """Responde uma questão de múltipla escolha"""
        log_progress("Bot respondendo questão de múltipla escolha...")

        # Conta opções disponíveis
        total_options = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_LIST)
        num_options = len(total_options)
        logger.info(f"📊 Questão com {num_options} opções disponíveis")

        if num_options == 0:
            logger.error("Nenhuma opção encontrada")
            return False

        # Loop até encontrar resposta correta
        attempt = 0
        while True:
            attempt += 1
            log_retry(f"Tentativa {attempt}")

            # Verifica se já foi respondida
            if self.driver_manager.find_elements(By.CSS_SELECTOR, f'{Config.Selectors.OPTION_LIST} {Config.Selectors.ICON_CHECK}'):
                log_celebration("Questão já respondida corretamente!")
                return True

            # Encontra opções
            options = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_SPAN)
            if not options:
                options = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_LIST)

            if not options:
                logger.error("Nenhuma opção encontrada")
                return False

            # Filtra opções não escolhidas
            unchosen_options = []
            for i, option in enumerate(options):
                try:
                    # Busca elemento pai
                    option_element = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_SPAN)[i]
                    li_parent = option_element.find_element(By.XPATH, "./ancestor::li[contains(@class, 'option')]")
                    has_check = li_parent.find_elements(By.CSS_SELECTOR, Config.Selectors.ICON_CHECK)
                    has_cancel = li_parent.find_elements(By.CSS_SELECTOR, Config.Selectors.ICON_CANCEL)
                except:
                    try:
                        option_li = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_LIST)
                        if i < len(option_li):
                            li_current = option_li[i]
                            has_check = li_current.find_elements(By.CSS_SELECTOR, Config.Selectors.ICON_CHECK)
                            has_cancel = li_current.find_elements(By.CSS_SELECTOR, Config.Selectors.ICON_CANCEL)
                        else:
                            continue
                    except:
                        continue

                if not has_check and not has_cancel:
                    unchosen_options.append(i)

            if not unchosen_options:
                log_success("Todas as opções testadas")
                return False

            # Escolhe primeira opção não escolhida
            chosen_index = unchosen_options[0]
            logger.info(f"🎯 Escolhendo opção {chosen_index + 1}...")

            try:
                # Clica na opção
                log_click("Clicando na opção...")
                fresh_options = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_SPAN)
                if not fresh_options:
                    fresh_options = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_LIST)

                if chosen_index < len(fresh_options):
                    fresh_options[chosen_index].click()
                    log_success("Opção clicada, aguardando resposta...")

                    # IMPORTANTE: Aguarda um tempo fixo após o clique para garantir carregamento
                    logger.info(f"⏳ Aguardando {Config.WAIT_AFTER_CLICK}s para página processar...")
                    time.sleep(Config.WAIT_AFTER_CLICK)
                else:
                    logger.error("Índice de opção inválido")
                    continue

                # Aguarda resposta com timeout maior
                wait = WebDriverWait(self.driver, 10)  # Aumentado de 8 para 10 segundos
                try:
                    wait.until(lambda d:
                        len(d.find_elements(By.CSS_SELECTOR, f'{Config.Selectors.OPTION_LIST} {Config.Selectors.ICON_CHECK}')) > 0 or
                        len(d.find_elements(By.CSS_SELECTOR, f'{Config.Selectors.OPTION_LIST} {Config.Selectors.ICON_CANCEL}')) > 0
                    )

                    # Verifica se acertou
                    verification_options = self.driver_manager.find_elements(By.CSS_SELECTOR, Config.Selectors.OPTION_LIST)
                    if chosen_index < len(verification_options):
                        li_verification = verification_options[chosen_index]
                        is_correct = li_verification.find_elements(By.CSS_SELECTOR, Config.Selectors.ICON_CHECK)
                    else:
                        is_correct = self.driver_manager.find_elements(
                            By.CSS_SELECTOR,
                            f'{Config.Selectors.OPTION_LIST} {Config.Selectors.ICON_CHECK}'
                        )

                    if is_correct:
                        log_celebration("Questão respondida corretamente!")
                        return True
                    else:
                        logger.error("Opção incorreta, tentando próxima...")
                        continue

                except:
                    logger.warning("Timeout aguardando resposta, tentando próxima opção...")
                    continue

            except Exception as e:
                logger.error(f"Erro ao clicar na opção: {str(e)}")
                if "stale element" in str(e).lower():
                    logger.warning("Erro de elemento obsoleto, aguardando 2 segundos...")
                    time.sleep(2)
                continue

    def process_question(self, question_num: int, total: int) -> bool:
        """
        Processa uma questão

        Args:
            question_num: Número da questão
            total: Total de questões

        Returns:
            True se processou com sucesso, False caso contrário
        """
        try:
            # Detecta tipo da questão
            question_type = self.detect_question_type()

            # Se não detectou, aguarda carregamento mínimo
            if question_type == QuestionType.UNKNOWN:
                question_type = self.wait_minimal_load()

            # Se ainda não detectou, aguarda carregamento completo
            if question_type == QuestionType.UNKNOWN:
                self.wait_complete_load()
                question_type = self.detect_question_type()

            # Se ainda não detectou, retorna False
            if question_type == QuestionType.UNKNOWN:
                logger.error("Questão não identificada")
                return False

            # Processa baseado no tipo
            if question_type == QuestionType.MULTIPLE_CHOICE:
                logger.info(f"\n📝 Questão {question_num}/{total} - Múltipla Escolha")
                return self.answer_multiple_choice_question()

            elif question_type == QuestionType.TEXT:
                logger.info(f"\n📝 Questão {question_num}/{total} - Texto")
                return self.answer_text_question()

            elif question_type == QuestionType.TEXT_ANSWERED:
                log_success("Questão de texto já respondida")
                return True

            elif question_type == QuestionType.MULTIPLE_CHOICE_ANSWERED:
                log_success("Questão de múltipla escolha já respondida")
                return True

            elif question_type == QuestionType.IMAGE:
                log_image("Questão de imagem - pulando")
                return True

            else:
                logger.error(f"Tipo de questão desconhecido: {question_type}")
                return False

        except Exception as e:
            logger.error(f"Erro ao processar questão: {str(e)}")
            return False

    def verify_answer(self, question_type: QuestionType) -> bool:
        """
        Verifica se a questão foi respondida corretamente

        Args:
            question_type: Tipo da questão

        Returns:
            True se foi respondida, False caso contrário
        """
        try:
            self.driver_manager.refresh()
            self.wait_minimal_load()

            result_type = self.detect_question_type()

            if question_type == QuestionType.MULTIPLE_CHOICE:
                return result_type == QuestionType.MULTIPLE_CHOICE_ANSWERED
            elif question_type == QuestionType.TEXT:
                return result_type == QuestionType.TEXT_ANSWERED

            return False

        except Exception as e:
            logger.error(f"Erro ao verificar resposta: {str(e)}")
            return False
