"""
Sistema de logging estruturado para o Memory Orchestrator
"""
import logging
import sys
from typing import Any, Dict
from datetime import datetime
import structlog
from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO") -> structlog.BoundLogger:
    """
    Configura logging estruturado com JSON para produção

    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logger configurado
    """

    # Configura handler com JSON formatter
    logHandler = logging.StreamHandler(sys.stdout)

    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logHandler.setFormatter(formatter)

    # Configura root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[logHandler]
    )

    # Configura structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


# Logger global
logger = setup_logging()


class RequestLogger:
    """Helper para logging de requests com métricas"""

    def __init__(self):
        self.logger = structlog.get_logger()

    def log_request(
        self,
        request_id: str,
        persona: str,
        model: str,
        message_count: int,
        stream: bool = False
    ) -> None:
        """Log de request recebido"""
        self.logger.info(
            "request_received",
            request_id=request_id,
            persona=persona,
            model=model,
            message_count=message_count,
            stream=stream
        )

    def log_memory_retrieval(
        self,
        request_id: str,
        query: str,
        memories_found: int,
        retrieval_time_ms: float
    ) -> None:
        """Log de busca de memória"""
        self.logger.info(
            "memory_retrieval",
            request_id=request_id,
            query=query[:100],  # Limita tamanho
            memories_found=memories_found,
            retrieval_time_ms=round(retrieval_time_ms, 2)
        )

    def log_model_selection(
        self,
        request_id: str,
        selected_model: str,
        reason: str,
        auto_routed: bool = False
    ) -> None:
        """Log de seleção de modelo"""
        self.logger.info(
            "model_selected",
            request_id=request_id,
            model=selected_model,
            reason=reason,
            auto_routed=auto_routed
        )

    def log_response(
        self,
        request_id: str,
        model: str,
        total_time_ms: float,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        memories_used: int
    ) -> None:
        """Log de response completo"""
        self.logger.info(
            "response_sent",
            request_id=request_id,
            model=model,
            total_time_ms=round(total_time_ms, 2),
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=round(cost_usd, 4),
            memories_used=memories_used
        )

    def log_error(
        self,
        request_id: str,
        error_type: str,
        error_message: str,
        **kwargs: Any
    ) -> None:
        """Log de erro"""
        self.logger.error(
            "request_error",
            request_id=request_id,
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )

    def log_memory_storage(
        self,
        request_id: str,
        stored: bool,
        reason: str,
        entities_extracted: int = 0
    ) -> None:
        """Log de armazenamento de memória"""
        self.logger.info(
            "memory_storage",
            request_id=request_id,
            stored=stored,
            reason=reason,
            entities_extracted=entities_extracted
        )


# Instância global
request_logger = RequestLogger()
