from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from ..runtime.base import RuntimeAction, RuntimeObservation


@dataclass
class AIPlan:
    """One step decided by the AI: an action to run, plus optional 'done' signal."""
    action: RuntimeAction | None = None
    done: bool = False
    final_answer: Any = None
    reasoning: str = ""


@dataclass
class AIContext:
    goal: str
    history: list[dict[str, Any]] = field(default_factory=list)
    max_steps: int = 25
    mode: str = "browser"


class AIBackend(abc.ABC):
    name: str = "abstract"

    @abc.abstractmethod
    async def next_step(self, ctx: AIContext, observation: RuntimeObservation) -> AIPlan: ...
