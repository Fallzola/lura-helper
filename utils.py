"""
Funções utilitárias
"""
import time
from pathlib import Path
from typing import List

from logger import logger, log_success


def load_links_from_file(file_path: Path) -> List[str]:
    """
    Carrega links do arquivo

    Args:
        file_path: Caminho do arquivo de links

    Returns:
        Lista de links
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            links = [line.strip() for line in file if line.strip()]
        return links
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Erro ao ler arquivo: {str(e)}")
        return []


def format_time(seconds: float) -> str:
    """
    Formata segundos em formato HH:MM:SS

    Args:
        seconds: Tempo em segundos

    Returns:
        String formatada
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_timestamp(timestamp: float) -> str:
    """
    Formata timestamp em HH:MM:SS

    Args:
        timestamp: Timestamp Unix

    Returns:
        String formatada
    """
    return time.strftime('%H:%M:%S', time.localtime(timestamp))


class Timer:
    """Classe para gerenciar tempo de execução"""

    def __init__(self, description: str = ""):
        self.description = description
        self.start_time = None
        self.end_time = None

    def start(self):
        """Inicia o timer"""
        self.start_time = time.time()
        if self.description:
            logger.info(f"⏱️  {self.description} - Início: {format_timestamp(self.start_time)}")

    def stop(self):
        """Para o timer"""
        self.end_time = time.time()
        if self.description:
            duration = self.end_time - self.start_time
            logger.info(f"⏱️  {self.description} - Duração: {duration:.1f}s")
        return self.elapsed()

    def elapsed(self) -> float:
        """Retorna tempo decorrido"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def print_summary(total_questions: int, failed_questions: List, total_time: float):
    """
    Imprime sumário da execução

    Args:
        total_questions: Total de questões processadas
        failed_questions: Lista de questões que falharam
        total_time: Tempo total de execução (inclui login e tudo)
    """
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMO GERAL DA EXECUÇÃO")
    logger.info("=" * 60)

    # Estatísticas de questões
    successful_questions = total_questions - len(failed_questions)
    success_rate = (successful_questions / total_questions * 100) if total_questions > 0 else 0

    logger.info(f"📝 Total de questões: {total_questions}")
    logger.info(f"✅ Questões bem-sucedidas: {successful_questions}")
    logger.info(f"❌ Questões com falha: {len(failed_questions)}")
    logger.info(f"📈 Taxa de sucesso: {success_rate:.1f}%")

    # Estatísticas de tempo
    logger.info(f"\n⏱️  Tempo total de execução (login + exercícios): {format_time(total_time)}")
    if total_questions > 0:
        avg_time = total_time / total_questions
        logger.info(f"⏱️  Tempo médio por questão: {avg_time:.1f}s")

    # Lista de questões que falharam
    if failed_questions:
        logger.info(f"\n❌ QUESTÕES QUE FALHARAM ({len(failed_questions)}):")
        for idx, link in failed_questions:
            logger.info(f"   • Questão {idx}: {link}")
    else:
        logger.info("\n🎉 TODAS AS QUESTÕES FORAM RESOLVIDAS COM SUCESSO!")

    logger.info("=" * 60)


def validate_url(url: str) -> bool:
    """
    Valida se a URL é do Plurall

    Args:
        url: URL a validar

    Returns:
        True se válida, False caso contrário
    """
    return "atividades.plurall.net" in url and "/exercicio/" in url


def extract_question_id(url: str) -> str:
    """
    Extrai o ID da questão da URL

    Args:
        url: URL da questão

    Returns:
        ID da questão
    """
    import re
    match = re.search(r'/exercicio/(\d+)/', url)
    return match.group(1) if match else "unknown"
