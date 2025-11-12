#!/usr/bin/env python3
"""
Bot Automático do Plurall - Versão Refatorada
Automatiza a resolução de atividades da plataforma Plurall

Autor: Refatorado com IA
Data: 2025-11-11
"""
import sys
import time
from typing import List, Tuple

from config import Config
from logger import logger, log_start, log_success, log_progress, log_timer, log_link, log_celebration
from exceptions import PluralBotException
from webdriver_manager import WebDriverManager
from question_handler import QuestionHandler, QuestionType
from api_client import PluralAPIClient
from utils import load_links_from_file, Timer, print_summary, validate_url, format_time


class PluralBot:
    """Classe principal do bot do Plurall"""

    def __init__(self, links_file: str = None):
        """
        Inicializa o bot

        Args:
            links_file: Caminho do arquivo de links (opcional)
        """
        self.links_file = Config.get_links_file() if not links_file else links_file
        self.driver_manager = None
        self.question_handler = None
        self.api_client = None
        self.failed_questions: List[Tuple[int, str]] = []
        self.exercises_timer = None  # Timer para todos os exercícios
        self.exercises_start_time = None  # Timestamp do início dos exercícios

    def initialize(self):
        """Inicializa componentes do bot"""
        log_start("Iniciando bot do Plurall...")

        try:
            # Valida configuração
            Config.validate_config()

            # Inicializa WebDriver
            self.driver_manager = WebDriverManager()
            self.driver_manager.initialize_driver()

            # Inicializa handlers
            self.question_handler = QuestionHandler(self.driver_manager)
            self.api_client = PluralAPIClient(self.driver_manager)

            log_success("Bot inicializado com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao inicializar bot: {str(e)}")
            raise PluralBotException(f"Falha na inicialização: {str(e)}")

    def load_exercise_links(self) -> List[str]:
        """
        Carrega links dos exercícios

        Returns:
            Lista de links
        """
        log_progress("Carregando links dos exercícios...")
        links = load_links_from_file(self.links_file)

        if not links:
            logger.error("Nenhum link encontrado!")
            return []

        # Valida links
        valid_links = [link for link in links if validate_url(link)]

        if len(valid_links) != len(links):
            logger.warning(f"⚠️  {len(links) - len(valid_links)} links inválidos foram ignorados")

        logger.info(f"📚 Carregados {len(valid_links)} links de exercícios")
        return valid_links

    def process_question(self, question_num: int, total: int, link: str) -> bool:
        """
        Processa uma questão individual

        Args:
            question_num: Número da questão
            total: Total de questões
            link: Link do exercício

        Returns:
            True se processou com sucesso, False caso contrário
        """
        with Timer(f"Questão {question_num}"):
            log_progress(f"\n📝 Questão {question_num}/{total}")
            log_link(f"Link: {link}")

            try:
                # Navega para o link
                self.driver_manager.navigate_to(link)

                # Detecta tipo da questão
                question_type = self.question_handler.detect_question_type()

                # Se não conseguiu detectar, aguarda carregamento mínimo
                if question_type == QuestionType.UNKNOWN:
                    logger.warning("Detecção imediata falhou, aguardando carregamento mínimo...")
                    question_type = self.question_handler.wait_minimal_load()

                # Se ainda não conseguiu detectar, aguarda carregamento completo
                if question_type == QuestionType.UNKNOWN:
                    logger.warning("Carregamento mínimo falhou, tentando carregamento completo...")
                    self.question_handler.wait_complete_load()
                    question_type = self.question_handler.detect_question_type()

                # Se ainda não conseguiu detectar, pula
                if question_type == QuestionType.UNKNOWN:
                    logger.error("Questão não identificada mesmo após todas as tentativas")
                    return False

                # Processa a questão
                success = self.question_handler.process_question(question_num, total)

                if not success:
                    logger.error(f"Questão {question_num} falhou")
                    return False

                # Verifica se foi respondida
                if question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TEXT]:
                    verified = self.question_handler.verify_answer(question_type)
                    if not verified:
                        logger.warning(f"Verificação falhou para questão {question_num}")
                        return False

                log_success(f"Questão {question_num} processada com sucesso!")
                return True

            except Exception as e:
                logger.error(f"Erro ao processar questão {question_num}: {str(e)}")
                return False

    def first_pass(self, links: List[str]) -> List[Tuple[int, str]]:
        """
        Primeira passada: processa todas as questões

        Args:
            links: Lista de links

        Returns:
            Lista de questões que falharam
        """
        log_start("INICIANDO PRIMEIRA PASSADA...")
        failed = []

        # Inicia o timer dos exercícios no primeiro exercício
        if self.exercises_timer is None:
            self.exercises_timer = Timer("Todos os Exercícios")
            self.exercises_timer.start()
            self.exercises_start_time = time.time()
            logger.info("⏱️  Timer dos exercícios iniciado!")

        for i, link in enumerate(links, 1):
            success = self.process_question(i, len(links), link)

            if not success:
                failed.append((i, link))
                logger.warning(f"Questão {i} falhou - será retentada depois")

        return failed

    def second_pass(self, failed_questions: List[Tuple[int, str]], total: int):
        """
        Segunda passada: retenta questões que falharam

        Args:
            failed_questions: Lista de questões que falharam
            total: Total de questões
        """
        if not failed_questions:
            return

        log_start(f"INICIANDO SEGUNDA PASSADA - {len(failed_questions)} questões para retentar...")

        for i, (original_idx, link) in enumerate(failed_questions, 1):
            log_progress(f"\n🔄 Retentando questão {original_idx} ({i}/{len(failed_questions)})")
            log_link(f"Link: {link}")

            try:
                # Navega para o link
                self.driver_manager.navigate_to(link)

                # Aguarda carregamento completo
                self.question_handler.wait_complete_load()

                # Processa questão
                success = self.question_handler.process_question(original_idx, total)

                if success:
                    log_success(f"Questão {original_idx} resolvida na segunda tentativa!")
                    # Remove da lista de falhas
                    self.failed_questions.remove((original_idx, link))
                else:
                    logger.error(f"Questão {original_idx} falhou novamente")

            except Exception as e:
                logger.error(f"Erro ao retentar questão {original_idx}: {str(e)}")
                continue

    def run(self):
        """Executa o bot"""
        total_timer = Timer("Execução Total (incluindo login)")
        total_timer.start()

        try:
            # Inicializa
            self.initialize()

            # Aguarda login
            self.driver_manager.wait_for_login()

            # Carrega links
            links = self.load_exercise_links()
            if not links:
                logger.error("Nenhum link para processar!")
                return

            # Primeira passada (timer dos exercícios inicia aqui)
            self.failed_questions = self.first_pass(links)

            # Segunda passada
            self.second_pass(self.failed_questions, len(links))

            # Para o timer dos exercícios
            if self.exercises_timer:
                exercises_time = self.exercises_timer.stop()
                logger.info("\n" + "=" * 60)
                logger.info("⏱️  TEMPO DOS EXERCÍCIOS (do primeiro ao último):")
                logger.info(f"⏰ Início: {time.strftime('%H:%M:%S', time.localtime(self.exercises_start_time))}")
                logger.info(f"⏰ Fim: {time.strftime('%H:%M:%S', time.localtime(time.time()))}")
                logger.info(f"⏱️  Duração: {format_time(exercises_time)}")
                logger.info(f"⏱️  Total em segundos: {exercises_time:.1f}s")
                logger.info("=" * 60)

            # Resultado final
            log_celebration("Processamento concluído!")

        except KeyboardInterrupt:
            logger.info("\n⏹️  Programa interrompido pelo usuário.")
            sys.exit(0)

        except Exception as e:
            logger.error(f"Erro geral: {str(e)}")

        finally:
            # Para timer total
            total_time = total_timer.stop()

            # Imprime sumário
            if 'links' in locals():
                print_summary(len(links), self.failed_questions, total_time)

            # Fecha navegador
            if self.driver_manager:
                self.driver_manager.quit()

            logger.info("👋 Bot finalizado!")


def main():
    """Função principal"""
    try:
        # Cria e executa o bot
        bot = PluralBot()
        bot.run()

    except Exception as e:
        logger.critical(f"Erro crítico: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
