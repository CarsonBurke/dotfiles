"""Conservative, framework-agnostic early-cull decision hook.

Call at coherent evaluation boundaries with already-smoothed, comparable metrics.
The hook never terminates work; the training framework owns pruning, checkpointing,
and process exit semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal, Mapping

__all__ = ["AutoCullHook", "CullDecision", "MetricSpec"]

Mode = Literal["max", "min"]


@dataclass(frozen=True, slots=True)
class MetricSpec:
    mode: Mode
    min_delta: float

    def __post_init__(self) -> None:
        if self.mode not in ("max", "min"):
            raise ValueError("mode must be 'max' or 'min'")
        if (
            isinstance(self.min_delta, bool)
            or not isinstance(self.min_delta, (int, float))
            or not isfinite(self.min_delta)
            or self.min_delta < 0
        ):
            raise ValueError("min_delta must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class CullDecision:
    should_cull: bool
    evaluations: int
    stale_evaluations: int
    improved_metrics: tuple[str, ...]
    reason: str | None = None


class AutoCullHook:
    """Cull after no configured signal materially improves for a full window."""

    _STATE_VERSION = 1

    def __init__(
        self,
        metrics: Mapping[str, MetricSpec],
        *,
        warmup_evaluations: int,
        patience_evaluations: int,
    ) -> None:
        if not metrics or any(
            not isinstance(name, str) or not name for name in metrics
        ):
            raise ValueError("at least one nonempty string metric name is required")
        if (
            isinstance(warmup_evaluations, bool)
            or not isinstance(warmup_evaluations, int)
            or warmup_evaluations < 1
        ):
            raise ValueError("warmup_evaluations must be an integer of at least 1")
        if (
            isinstance(patience_evaluations, bool)
            or not isinstance(patience_evaluations, int)
            or patience_evaluations < 2
        ):
            raise ValueError("patience_evaluations must be an integer of at least 2")

        self.metrics = dict(metrics)
        self.warmup_evaluations = warmup_evaluations
        self.patience_evaluations = patience_evaluations
        self._evaluations = 0
        self._best: dict[str, float] = {}
        self._stale_evaluations = 0
        self._culled = False

    def __call__(self, **metrics: float | None) -> CullDecision:
        return self.update(metrics)

    def update(self, metrics: Mapping[str, float | None]) -> CullDecision:
        observed: dict[str, float] = {}
        missing: list[str] = []
        for name in self.metrics:
            value = metrics.get(name)
            if value is None:
                missing.append(name)
                continue
            numeric = float(value)
            if not isfinite(numeric):
                raise ValueError(f"metric {name!r} must be finite")
            observed[name] = numeric

        if missing:
            raise ValueError(
                "evaluation is missing configured metrics: " + ", ".join(missing)
            )
        if self._culled:
            return self._decision(())

        self._evaluations += 1
        if self._evaluations <= self.warmup_evaluations:
            # Anchor patience at the end of warmup, not at an early noisy extreme.
            self._best.update(observed)
            return self._decision(())

        improved: list[str] = []
        for name, value in observed.items():
            best = self._best.get(name)
            if best is None or self._improved(value, best, self.metrics[name]):
                self._best[name] = value
                improved.append(name)

        if improved:
            self._stale_evaluations = 0
        else:
            self._stale_evaluations += 1
            self._culled = self._stale_evaluations >= self.patience_evaluations

        return self._decision(tuple(improved))

    def state_dict(self) -> dict[str, object]:
        return {
            "version": self._STATE_VERSION,
            "signature": self._signature(),
            "evaluations": self._evaluations,
            "best": dict(self._best),
            "stale_evaluations": self._stale_evaluations,
            "culled": self._culled,
        }

    def load_state_dict(self, state: Mapping[str, object]) -> None:
        if state.get("version") != self._STATE_VERSION:
            raise ValueError("unsupported autocull state version")
        if state.get("signature") != self._signature():
            raise ValueError("autocull state does not match this hook configuration")

        try:
            evaluations = state["evaluations"]
            stale = state["stale_evaluations"]
            raw_best = state["best"]
            culled = state["culled"]
        except KeyError as error:
            raise ValueError(f"autocull state is missing {error.args[0]!r}") from error

        if (
            isinstance(evaluations, bool)
            or not isinstance(evaluations, int)
            or isinstance(stale, bool)
            or not isinstance(stale, int)
            or not isinstance(raw_best, Mapping)
            or not isinstance(culled, bool)
            or evaluations < 0
            or stale < 0
            or stale > max(0, evaluations - self.warmup_evaluations)
            or (culled and stale != self.patience_evaluations)
            or (not culled and stale >= self.patience_evaluations)
        ):
            raise ValueError("invalid autocull state")

        best: dict[str, float] = {}
        for name, value in raw_best.items():
            if name not in self.metrics:
                raise ValueError(f"unknown metric in autocull state: {name!r}")
            numeric = float(value)
            if not isfinite(numeric):
                raise ValueError(f"non-finite metric in autocull state: {name!r}")
            best[str(name)] = numeric

        expected_metrics = set(self.metrics) if evaluations else set()
        if set(best) != expected_metrics:
            raise ValueError("autocull state has incomplete metric baselines")

        self._evaluations = evaluations
        self._best = best
        self._stale_evaluations = stale
        self._culled = culled

    @staticmethod
    def _improved(value: float, best: float, spec: MetricSpec) -> bool:
        delta = value - best if spec.mode == "max" else best - value
        return delta > spec.min_delta

    def _decision(self, improved: tuple[str, ...]) -> CullDecision:
        reason = None
        if self._culled:
            reason = (
                "no configured metric materially improved for "
                f"{self._stale_evaluations} evaluation(s) after "
                f"{self.warmup_evaluations} warmup evaluation(s)"
            )
        return CullDecision(
            should_cull=self._culled,
            evaluations=self._evaluations,
            stale_evaluations=self._stale_evaluations,
            improved_metrics=improved,
            reason=reason,
        )

    def _signature(self) -> dict[str, object]:
        return {
            "metrics": {
                name: {"mode": spec.mode, "min_delta": spec.min_delta}
                for name, spec in self.metrics.items()
            },
            "warmup_evaluations": self.warmup_evaluations,
            "patience_evaluations": self.patience_evaluations,
        }
