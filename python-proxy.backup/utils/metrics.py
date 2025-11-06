"""
Sistema de métricas e tracking de custos
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import threading
from config import MODEL_CONFIGS


class MetricsTracker:
    """Rastreador de métricas e custos"""

    def __init__(self):
        self._lock = threading.Lock()
        self._metrics: Dict = {
            "requests": defaultdict(int),
            "tokens": defaultdict(lambda: {"input": 0, "output": 0}),
            "costs": defaultdict(float),
            "models": defaultdict(int),
            "personas": defaultdict(int),
            "memories": defaultdict(int),
            "errors": defaultdict(int),
            "response_times": [],
            "start_time": datetime.now()
        }

    def track_request(
        self,
        model: str,
        persona: str,
        tokens_input: int,
        tokens_output: int,
        response_time_ms: float,
        memories_used: int = 0,
        error: bool = False
    ) -> Dict:
        """
        Registra uma request e calcula custos

        Returns:
            Dicionário com métricas da request
        """
        with self._lock:
            # Contadores básicos
            self._metrics["requests"]["total"] += 1
            self._metrics["models"][model] += 1
            self._metrics["personas"][persona] += 1

            if error:
                self._metrics["errors"]["total"] += 1
                self._metrics["errors"][model] += 1
                return {"error": True}

            # Tokens
            self._metrics["tokens"][model]["input"] += tokens_input
            self._metrics["tokens"][model]["output"] += tokens_output
            self._metrics["tokens"]["total"]["input"] += tokens_input
            self._metrics["tokens"]["total"]["output"] += tokens_output

            # Memórias
            self._metrics["memories"]["used"] += memories_used
            self._metrics["memories"]["requests_with_memory"] += (1 if memories_used > 0 else 0)

            # Tempo de resposta
            self._metrics["response_times"].append(response_time_ms)

            # Calcula custo
            cost = self._calculate_cost(model, tokens_input, tokens_output)
            self._metrics["costs"][model] += cost
            self._metrics["costs"]["total"] += cost

            return {
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "cost_usd": cost,
                "response_time_ms": response_time_ms,
                "memories_used": memories_used
            }

    def _calculate_cost(
        self,
        model: str,
        tokens_input: int,
        tokens_output: int
    ) -> float:
        """Calcula custo baseado no modelo e tokens"""
        if model not in MODEL_CONFIGS:
            return 0.0

        config = MODEL_CONFIGS[model]
        cost_input = (tokens_input / 1000) * config["cost_per_1k_input"]
        cost_output = (tokens_output / 1000) * config["cost_per_1k_output"]

        return cost_input + cost_output

    def get_stats(self, period: str = "all") -> Dict:
        """
        Retorna estatísticas agregadas

        Args:
            period: 'all', 'today', 'week', 'month'

        Returns:
            Dicionário com estatísticas
        """
        with self._lock:
            response_times = self._metrics["response_times"]
            total_requests = self._metrics["requests"]["total"]

            stats = {
                "summary": {
                    "total_requests": total_requests,
                    "total_cost_usd": round(self._metrics["costs"]["total"], 4),
                    "total_tokens_input": self._metrics["tokens"]["total"]["input"],
                    "total_tokens_output": self._metrics["tokens"]["total"]["output"],
                    "avg_response_time_ms": (
                        round(sum(response_times) / len(response_times), 2)
                        if response_times else 0
                    ),
                    "uptime_seconds": (datetime.now() - self._metrics["start_time"]).total_seconds()
                },
                "by_model": self._format_model_stats(),
                "by_persona": dict(self._metrics["personas"]),
                "memory": {
                    "total_memories_used": self._metrics["memories"]["used"],
                    "requests_with_memory": self._metrics["memories"]["requests_with_memory"],
                    "hit_rate": (
                        round(
                            self._metrics["memories"]["requests_with_memory"] / total_requests * 100,
                            2
                        ) if total_requests > 0 else 0
                    )
                },
                "errors": {
                    "total": self._metrics["errors"]["total"],
                    "by_model": dict(self._metrics["errors"])
                }
            }

            return stats

    def _format_model_stats(self) -> Dict:
        """Formata estatísticas por modelo"""
        model_stats = {}

        for model, count in self._metrics["models"].items():
            tokens = self._metrics["tokens"][model]
            cost = self._metrics["costs"][model]

            model_stats[model] = {
                "requests": count,
                "tokens_input": tokens["input"],
                "tokens_output": tokens["output"],
                "cost_usd": round(cost, 4)
            }

        return model_stats

    def reset_metrics(self) -> None:
        """Reset de todas as métricas"""
        with self._lock:
            self._metrics = {
                "requests": defaultdict(int),
                "tokens": defaultdict(lambda: {"input": 0, "output": 0}),
                "costs": defaultdict(float),
                "models": defaultdict(int),
                "personas": defaultdict(int),
                "memories": defaultdict(int),
                "errors": defaultdict(int),
                "response_times": [],
                "start_time": datetime.now()
            }

    def check_cost_alert(self, threshold: float) -> Optional[Dict]:
        """Verifica se ultrapassou threshold de custo"""
        total_cost = self._metrics["costs"]["total"]

        if total_cost >= threshold:
            return {
                "alert": True,
                "threshold": threshold,
                "current_cost": round(total_cost, 4),
                "message": f"Cost threshold exceeded: ${total_cost:.4f} >= ${threshold:.2f}"
            }

        return None


# Instância global
metrics_tracker = MetricsTracker()
