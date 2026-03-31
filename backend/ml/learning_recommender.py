"""
Adaptive Learning module recommendation engine.

This file is responsible for:
- defining the learning module registry (12 modules)
- scoring/filtering modules based on user metrics
- excluding completed modules
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class LearningModule:
    module_key: str
    title: str
    module_topic: str
    summary: str
    steps: List[str]
    actions: List[str]


def get_module_registry() -> List[LearningModule]:
    # Note: topic is used in Ollama prompt generation.
    return [
        LearningModule(
            module_key="budgeting_basics",
            title="Budgeting Basics",
            module_topic="budgeting basics for students and gig workers",
            summary="Build a simple budget that actually works even with irregular income.",
            steps=[
                "Identify your essential needs vs discretionary wants.",
                "Create a lightweight plan for essentials first.",
                "Review weekly and adjust before the month gets off track."
            ],
            actions=[
                "Make a budget: essentials + wants + a savings line.",
                "Do a 10-minute weekly review every Sunday."
            ],
        ),
        LearningModule(
            module_key="needs_vs_wants",
            title="Needs vs Wants Mastery",
            module_topic="needs vs wants decision rules",
            summary="Protect needs and control wants so your runway lasts longer.",
            steps=[
                "Learn how to classify spending as need or want.",
                "Use a want-wait rule for non-essential purchases.",
                "Reduce wants when survival days are low."
            ],
            actions=[
                "List 3 want categories you will cap this week.",
                "Delay discretionary purchases by 24 hours."
            ],
        ),
        LearningModule(
            module_key="emergency_fund_planning",
            title="Emergency Fund Planning",
            module_topic="emergency fund planning",
            summary="Create a safety buffer so unexpected expenses do not break your plan.",
            steps=[
                "Understand the purpose of an emergency fund.",
                "Start small and keep it separate from daily spending.",
                "Build gradually until you reach a safer runway."
            ],
            actions=[
                "Pick a starter goal (example: 10,000).",
                "Automate a small transfer on payday."
            ],
        ),
        LearningModule(
            module_key="spending_discipline",
            title="Spending Discipline",
            module_topic="spending discipline and habit building",
            summary="Reduce impulsive outflow and stabilize your spending pattern.",
            steps=[
                "Find your biggest spending leak category.",
                "Create weekly caps for discretionary areas.",
                "Use a wish-list and revisit purchases later."
            ],
            actions=[
                "Set a weekly cap for your top category.",
                "Add 2-3 items to a wish-list and review after a week."
            ],
        ),
        LearningModule(
            module_key="savings_consistency",
            title="Savings Consistency",
            module_topic="savings consistency strategies",
            summary="Turn savings into a habit and gradually improve it.",
            steps=[
                "Prioritize savings at income arrival.",
                "Measure savings rate and adjust target.",
                "Keep it sustainable, not extreme."
            ],
            actions=[
                "Choose an initial savings % based on your savings rate.",
                "Review progress weekly."
            ],
        ),
        LearningModule(
            module_key="income_tracking",
            title="Income Tracking",
            module_topic="income tracking for irregular income",
            summary="Understand your inflow stability and plan spending safely.",
            steps=[
                "Track each income source consistently.",
                "Estimate variability and plan for worst-case months.",
                "Use stable baselines for essentials."
            ],
            actions=[
                "Categorize all income sources the same way.",
                "Track variability weekly."
            ],
        ),
        LearningModule(
            module_key="survival_budget_planning",
            title="Survival Budget Planning",
            module_topic="survival-first budget planning",
            summary="When runway is low, switch to an essentials-only plan quickly.",
            steps=[
                "Define essentials-only rules.",
                "Pause non-essentials temporarily.",
                "Rebuild buffer before growth steps."
            ],
            actions=[
                "Set a temporary daily spend cap for essentials.",
                "Pause 1-2 non-essential categories for 2 weeks."
            ],
        ),
        LearningModule(
            module_key="investment_basics",
            title="Investment Basics",
            module_topic="investment basics and long-term discipline",
            summary="Learn fundamentals before investing your money.",
            steps=[
                "Build emergency fund first (protect downside).",
                "Start with low-cost diversified options.",
                "Focus on long-term consistency."
            ],
            actions=[
                "Decide your first investment amount (small and regular).",
                "Automate contributions if possible."
            ],
        ),
        LearningModule(
            module_key="expense_optimization",
            title="Expense Optimization",
            module_topic="expense optimization and category efficiency",
            summary="Cut costs intelligently without harming your essentials.",
            steps=[
                "Use your dominant category share to target improvements.",
                "Find recurring waste and negotiate or switch options.",
                "Plan big purchases ahead instead of reactive spending."
            ],
            actions=[
                "Reduce your dominant category spend by 10-20%.",
                "Set aside a small bucket for planned big purchases."
            ],
        ),
        LearningModule(
            module_key="wealth_building",
            title="Wealth Building",
            module_topic="wealth building for long-term growth",
            summary="Grow wealth gradually by protecting runway and improving savings.",
            steps=[
                "Avoid lifestyle inflation during income growth.",
                "Improve savings rate sustainably.",
                "Increase consistency before complexity."
            ],
            actions=[
                "Set a 3-month savings-rate target.",
                "Review and iterate every week."
            ],
        ),
        LearningModule(
            module_key="irregular_income_planning",
            title="Irregular Income Planning",
            module_topic="irregular income planning and runway management",
            summary="Stabilize your budget when income is unpredictable.",
            steps=[
                "Save from high-income months.",
                "Use conservative baseline spending.",
                "Treat income spikes as savings fuel, not spending fuel."
            ],
            actions=[
                "Pick a % to save from each income arrival.",
                "Stay survival-first until stability improves."
            ],
        ),
        LearningModule(
            module_key="daily_earning_discipline",
            title="Daily Earning Discipline",
            module_topic="daily earning discipline",
            summary="Use daily targets to avoid running out of cash.",
            steps=[
                "Convert monthly goals into daily actions.",
                "Prioritize essentials vs wants when runway is low.",
                "Track weekly progress and adjust quickly."
            ],
            actions=[
                "Set your daily target in Analytics.",
                "If you miss your target, reduce wants immediately."
            ],
        ),
    ]


def _safe_num(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def get_recommendations(
    metrics: Dict[str, Any],
    personality: str | None,
    completed_module_keys: set[str],
    top_k: int = 6,
) -> List[Dict[str, Any]]:
    """
    Compute recommended modules and return a ranked list of module metadata.
    """
    savings_rate = _safe_num(metrics.get("savings_rate_percent"))
    survival_days = _safe_num(metrics.get("survival_days"))
    expense_ratio = _safe_num(metrics.get("expense_ratio"))
    income_stability_score = _safe_num(metrics.get("income_stability_score"), default=0.5)
    income_variability_index = _safe_num(metrics.get("income_variability_index"))
    dominant_category_share = _safe_num(metrics.get("dominant_category_share"))

    registry = get_module_registry()

    # Quick helper to avoid returning completed modules.
    def not_completed(m: LearningModule) -> bool:
        return m.module_key not in completed_module_keys

    scored: List[tuple[LearningModule, float]] = []

    for m in registry:
        if not_completed(m) is False:
            continue

        score = 0.0

        if m.module_key == "budgeting_basics":
            score += max(0.0, 20.0 - savings_rate)  # low savings => higher score
            score += max(0.0, expense_ratio * 30.0)

        elif m.module_key == "needs_vs_wants":
            # spending discipline when runway is low or expense ratio is high
            score += max(0.0, 25.0 - survival_days)
            score += max(0.0, expense_ratio * 40.0)

        elif m.module_key == "emergency_fund_planning":
            score += max(0.0, 30.0 - survival_days) * 1.4

        elif m.module_key == "spending_discipline":
            score += max(0.0, expense_ratio * 60.0)
            score += max(0.0, (30.0 - survival_days)) * 0.5

        elif m.module_key == "savings_consistency":
            score += max(0.0, 18.0 - savings_rate) * 2.0

        elif m.module_key == "income_tracking":
            # low stability => higher score
            score += max(0.0, 0.9 - income_stability_score) * 60.0
            score += max(0.0, income_variability_index) * 30.0

        elif m.module_key == "survival_budget_planning":
            score += max(0.0, 14.0 - survival_days) * 3.0

        elif m.module_key == "investment_basics":
            # only when runway is safe enough
            score += max(0.0, survival_days - 30.0) * 0.3
            score += max(0.0, savings_rate - 15.0) * 1.0

        elif m.module_key == "expense_optimization":
            score += max(0.0, dominant_category_share - 0.30) * 200.0
            score += max(0.0, expense_ratio - 0.60) * 80.0

        elif m.module_key == "wealth_building":
            score += max(0.0, savings_rate - 20.0) * 1.5
            score += max(0.0, survival_days - 60.0) * 0.2

        elif m.module_key == "irregular_income_planning":
            # variability => irregular income planning
            score += max(0.0, income_variability_index - 0.40) * 120.0

        elif m.module_key == "daily_earning_discipline":
            score += max(0.0, 25.0 - survival_days) * 0.8

        # Slight personality bias
        if personality == "High-Spender":
            if m.module_key in {"spending_discipline", "needs_vs_wants", "expense_optimization"}:
                score *= 1.25
        if personality == "Saver":
            if m.module_key in {"investment_basics", "wealth_building", "savings_consistency"}:
                score *= 1.15

        # Ensure small positive scores so we still show something.
        scored.append((m, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    chosen = [m for m, _s in scored[:top_k] if _safe_num(_s, default=0.0) > 0.0]
    if not chosen:
        # fallback: return the top k by score even if all are zero
        chosen = [m for m, _s in scored[:top_k]]

    out: List[Dict[str, Any]] = []
    for i, m in enumerate(chosen):
        out.append({
            "rank": i + 1,
            "module_key": m.module_key,
            "title": m.title,
            "module_topic": m.module_topic,
            "summary": m.summary,
            "steps": m.steps,
            "actions": m.actions,
        })
    return out

