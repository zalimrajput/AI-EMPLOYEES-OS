"""Reporting tools: revenue, expense and sales-pipeline analytics.

Real aggregates are computed in Python from actual DB rows first; a single
model_router call only adds narrative commentary on top. If the LLM call
fails, the real numbers are still returned with a data-only narrative
(``source: "data"``) — figures are never lost or invented.
"""
import json
from datetime import date, datetime, time, timedelta, timezone

from dateutil.relativedelta import relativedelta

from app.ai import model_router
from app.ai.tools.base import ToolSpec

_PERIODS = {"last_7_days", "last_30_days", "last_quarter", "last_year", "month_to_date"}
_DEAL_TERMINAL_STAGES = {"won", "lost", "closed_won", "closed_lost", "archived"}
_DEAL_WON_STAGES = {"won", "closed_won"}
_DEAL_LOST_STAGES = {"lost", "closed_lost"}
_TOP_LIMIT = 5
_TEXT_LIMIT = 600


def _truncate(value, limit=_TEXT_LIMIT) -> str:
    if value is None:
        return ""
    text = str(value)
    return text[:limit] + ("…" if len(text) > limit else "")


def _quarter_start(d: date) -> date:
    return date(d.year, ((d.month - 1) // 3) * 3 + 1, 1)


def _period_bounds(period: str):
    """Return (start, end) aware datetimes for an inclusive range."""
    now = datetime.now(timezone.utc)
    today = now.date()
    if period == "last_7_days":
        start = datetime.combine(today - timedelta(days=7), time.min, tzinfo=timezone.utc)
        return start, now
    if period == "last_30_days":
        start = datetime.combine(today - timedelta(days=30), time.min, tzinfo=timezone.utc)
        return start, now
    if period == "month_to_date":
        start = datetime.combine(today.replace(day=1), time.min, tzinfo=timezone.utc)
        return start, now
    if period == "last_quarter":
        current_q_start = datetime.combine(_quarter_start(today), time.min, tzinfo=timezone.utc)
        start = current_q_start - relativedelta(months=3)
        end = current_q_start - timedelta(microseconds=1)
        return start, end
    if period == "last_year":
        start = datetime.combine(date(today.year - 1, 1, 1), time.min, tzinfo=timezone.utc)
        end = datetime.combine(
            date(today.year, 1, 1), time.min, tzinfo=timezone.utc
        ) - timedelta(microseconds=1)
        return start, end
    return None


def _require_period(arguments: dict):
    """Validate the period argument before any DB work. Returns an error dict
    (a dict with an "error" key) when invalid, else the period string."""
    period = arguments.get("period")
    if not period or not isinstance(period, str):
        return {
            "error": (
                "period is required (one of: "
                + ", ".join(sorted(_PERIODS))
                + ")"
            )
        }
    if period not in _PERIODS:
        return {
            "error": (
                f"invalid period '{period}'; valid values are: "
                + ", ".join(sorted(_PERIODS))
            )
        }
    return period


def _parse_llm_json(raw) -> dict | None:
    if not raw or not isinstance(raw, str):
        return None
    text = raw.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _narrative_messages(report_name: str, data: dict) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                f"You are a financial analyst producing a {report_name} report. "
                "Respond with ONLY a JSON object using exactly these keys: "
                "narrative (2-3 sentences), observations (an array of at most "
                "3 short strings). Do not invent any numbers; only comment on "
                "the data provided."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(data, default=str),
        },
    ]


def _merge_insights(data: dict, llm: dict | None) -> tuple:
    """Merge LLM narrative/observations over data-only fallbacks."""
    if llm is None:
        return data["computed_narrative"], data["computed_observations"], "data"
    narrative = _truncate(llm.get("narrative"), 600) or data["computed_narrative"]
    observations = data["computed_observations"]
    raw_obs = llm.get("observations")
    if isinstance(raw_obs, list) and raw_obs:
        observations = [_truncate(str(o), 200) for o in raw_obs][:3]
    return narrative, observations, "llm"


# ------------------------------------------------------------------ revenue


def _computed_revenue_narrative(data: dict) -> str:
    if data["invoice_count"] == 0:
        return f"No paid invoices recorded in {data['period'].replace('_', ' ')}."
    return (
        f"Revenue in {data['period'].replace('_', ' ')} totalled "
        f"${data['total_revenue']:.2f} from {data['invoice_count']} paid "
        f"invoice(s), averaging ${data['average_invoice_value']:.2f} per invoice."
    )


def _gather_revenue_data(db, org_id, start, end, period) -> dict:
    from app.models.invoice import Invoice

    paid = (
        db.query(Invoice)
        .filter(
            Invoice.organization_id == org_id,
            Invoice.status == "paid",
            Invoice.created_at >= start,
            Invoice.created_at <= end,
        )
        .all()
    )
    total_revenue = round(sum(float(i.amount or 0) for i in paid), 2)
    invoice_count = len(paid)
    average_invoice_value = (
        round(total_revenue / invoice_count, 2) if invoice_count else 0.0
    )

    customer_ids = {i.customer_id for i in paid if i.customer_id is not None}
    name_map = {}
    if customer_ids:
        from app.models.customer import Customer

        rows = (
            db.query(Customer.id, Customer.name)
            .filter(Customer.id.in_(customer_ids))
            .all()
        )
        name_map = {str(r[0]): r[1] for r in rows}

    by_customer = {}
    for inv in paid:
        cid = inv.customer_id
        by_customer[cid] = by_customer.get(cid, 0.0) + float(inv.amount or 0)

    revenue_by_customer = []
    for cid, amount in sorted(by_customer.items(), key=lambda kv: kv[1], reverse=True):
        revenue_by_customer.append(
            {
                "customer_id": str(cid) if cid else None,
                "customer_name": name_map.get(str(cid)) if cid else None,
                "revenue": round(amount, 2),
            }
        )
        if len(revenue_by_customer) >= _TOP_LIMIT:
            break

    flags = []
    if (
        total_revenue > 0
        and revenue_by_customer
        and revenue_by_customer[0]["revenue"] / total_revenue >= 0.4
    ):
        share = round(revenue_by_customer[0]["revenue"] / total_revenue * 100, 1)
        flags.append(
            "Revenue concentration risk: "
            f"{revenue_by_customer[0]['customer_name'] or 'Unassigned'} "
            f"accounts for {share}% of revenue."
        )
    if invoice_count == 0:
        flags.append("No revenue recorded in the period.")

    observations = list(flags)
    if revenue_by_customer:
        top = revenue_by_customer[0]
        observations.append(
            f"Top customer {top['customer_name'] or 'Unassigned'} contributed "
            f"${top['revenue']:.2f}."
        )
    observations = observations[:3]

    return {
        "period": period,
        "total_revenue": total_revenue,
        "invoice_count": invoice_count,
        "average_invoice_value": average_invoice_value,
        "revenue_by_customer": revenue_by_customer,
        "flags": flags,
        "computed_narrative": _computed_revenue_narrative(
            {"period": period, "total_revenue": total_revenue, "invoice_count": invoice_count, "average_invoice_value": average_invoice_value}
        ),
        "computed_observations": observations,
    }


def _generate_revenue_report(db, org_id, user_id, arguments: dict):
    period = _require_period(arguments)
    if isinstance(period, dict):
        return period
    start, end = _period_bounds(period)

    data = _gather_revenue_data(db, org_id, start, end, period)

    llm = None
    try:
        raw = model_router.complete(
            _narrative_messages("revenue", data), temperature=0.2
        )
        llm = _parse_llm_json(raw)
    except Exception:  # noqa: BLE001 - rate limit / no key -> data-only fallback
        llm = None

    narrative, observations, source = _merge_insights(data, llm)
    return {
        "report": "revenue",
        "period": period,
        "total_revenue": data["total_revenue"],
        "invoice_count": data["invoice_count"],
        "average_invoice_value": data["average_invoice_value"],
        "revenue_by_customer": data["revenue_by_customer"],
        "narrative": narrative,
        "observations": observations,
        "source": source,
    }


# ------------------------------------------------------------------ expense


def _computed_expense_narrative(data: dict) -> str:
    if data["expense_count"] == 0:
        return f"No expenses recorded in {data['period'].replace('_', ' ')}."
    return (
        f"Expenses in {data['period'].replace('_', ' ')} totalled "
        f"${data['total_expenses']:.2f} across {data['expense_count']} "
        f"expense(s)."
    )


def _gather_expense_data(db, org_id, start, end, period) -> dict:
    from app.models.finance import Expense, ExpenseCategory

    start_date = start.date()
    end_date = end.date()
    expenses = (
        db.query(Expense)
        .filter(
            Expense.organization_id == org_id,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
        )
        .all()
    )
    total_expenses = round(sum(float(e.amount or 0) for e in expenses), 2)
    expense_count = len(expenses)

    category_names = {}
    for cat in (
        db.query(ExpenseCategory)
        .filter(ExpenseCategory.organization_id == org_id)
        .all()
    ):
        category_names[str(cat.id)] = cat.name

    by_category = {}
    for e in expenses:
        name = category_names.get(str(e.category_id)) if e.category_id else None
        name = name or "Uncategorized"
        by_category[name] = by_category.get(name, 0.0) + float(e.amount or 0)

    category_breakdown = [
        {"category": name, "amount": round(amount, 2)}
        for name, amount in sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)
    ][:_TOP_LIMIT]

    top_expenses = [
        {
            "title": e.title,
            "amount": round(float(e.amount or 0), 2),
            "date": e.expense_date.isoformat() if e.expense_date else None,
        }
        for e in sorted(expenses, key=lambda x: float(x.amount or 0), reverse=True)
    ][:_TOP_LIMIT]

    flags = []
    if (
        total_expenses > 0
        and by_category
        and max(by_category.values()) / total_expenses >= 0.5
    ):
        top_cat = max(by_category, key=by_category.get)
        share = round(max(by_category.values()) / total_expenses * 100, 1)
        flags.append(f"Spend concentration: {top_cat} is {share}% of expenses.")
    if expense_count == 0:
        flags.append("No expenses recorded in the period.")

    observations = list(flags)
    if top_expenses:
        observations.append(
            f"Largest expense: {top_expenses[0]['title']} "
            f"at ${top_expenses[0]['amount']:.2f}."
        )
    observations = observations[:3]

    return {
        "period": period,
        "total_expenses": total_expenses,
        "expense_count": expense_count,
        "by_category": category_breakdown,
        "top_expenses": top_expenses,
        "flags": flags,
        "computed_narrative": _computed_expense_narrative(
            {
                "period": period,
                "total_expenses": total_expenses,
                "expense_count": expense_count,
            }
        ),
        "computed_observations": observations,
    }


def _generate_expense_report(db, org_id, user_id, arguments: dict):
    period = _require_period(arguments)
    if isinstance(period, dict):
        return period
    start, end = _period_bounds(period)

    data = _gather_expense_data(db, org_id, start, end, period)

    llm = None
    try:
        raw = model_router.complete(
            _narrative_messages("expense", data), temperature=0.2
        )
        llm = _parse_llm_json(raw)
    except Exception:  # noqa: BLE001 - rate limit / no key -> data-only fallback
        llm = None

    narrative, observations, source = _merge_insights(data, llm)
    return {
        "report": "expense",
        "period": period,
        "total_expenses": data["total_expenses"],
        "expense_count": data["expense_count"],
        "by_category": data["by_category"],
        "top_expenses": data["top_expenses"],
        "narrative": narrative,
        "observations": observations,
        "source": source,
    }


# ----------------------------------------------------------- sales pipeline


def _computed_pipeline_narrative(data: dict) -> str:
    parts = [f"Open pipeline value is ${data['open_pipeline_value']:.2f}."]
    if data["closed_count"]:
        parts.append(
            f"{data['won_count']} deal(s) won (${data['won_value']:.2f}) and "
            f"{data['lost_count']} lost in {data['period'].replace('_', ' ')}, "
            f"a win rate of {round(data['win_rate'] * 100, 1)}%."
        )
    else:
        parts.append(f"No deals were closed in {data['period'].replace('_', ' ')}.")
    return " ".join(parts)


def _gather_pipeline_data(db, org_id, start, end, period) -> dict:
    from app.models.pipeline import Deal

    period_deals = (
        db.query(Deal)
        .filter(
            Deal.organization_id == org_id,
            Deal.created_at >= start,
            Deal.created_at <= end,
        )
        .all()
    )

    open_deals = [
        d
        for d in db.query(Deal).filter(Deal.organization_id == org_id).all()
        if (d.stage or "").lower() not in _DEAL_TERMINAL_STAGES
    ]
    open_pipeline_value = round(sum(float(d.value or 0) for d in open_deals), 2)

    won = [
        d for d in period_deals if (d.stage or "").lower() in _DEAL_WON_STAGES
    ]
    lost = [
        d for d in period_deals if (d.stage or "").lower() in _DEAL_LOST_STAGES
    ]
    won_value = round(sum(float(d.value or 0) for d in won), 2)
    won_count = len(won)
    lost_count = len(lost)
    closed_count = won_count + lost_count
    win_rate = round(won_count / closed_count, 3) if closed_count else None

    stage_map = {}
    for d in period_deals:
        stage = d.stage or "unknown"
        entry = stage_map.setdefault(stage, {"count": 0, "value": 0.0})
        entry["count"] += 1
        entry["value"] += float(d.value or 0)
    stage_distribution = [
        {"stage": stage, "count": entry["count"], "value": round(entry["value"], 2)}
        for stage, entry in sorted(stage_map.items(), key=lambda kv: kv[1]["value"], reverse=True)
    ]

    flags = []
    if closed_count == 0:
        flags.append("No deals closed in the period.")
    elif lost_count > 0 and won_count == 0:
        flags.append("All deals closed in the period were lost.")
    elif win_rate is not None and win_rate < 0.5:
        flags.append(f"Win rate is {round(win_rate * 100, 1)}%, below 50%.")

    observations = list(flags)
    if open_pipeline_value > 0:
        observations.append(f"Open pipeline is ${open_pipeline_value:.2f}.")
    observations = observations[:3]

    return {
        "period": period,
        "open_pipeline_value": open_pipeline_value,
        "won_value": won_value,
        "won_count": won_count,
        "lost_count": lost_count,
        "win_rate": win_rate,
        "stage_distribution": stage_distribution,
        "flags": flags,
        "closed_count": closed_count,
        "computed_narrative": _computed_pipeline_narrative(
            {
                "period": period,
                "open_pipeline_value": open_pipeline_value,
                "won_value": won_value,
                "won_count": won_count,
                "lost_count": lost_count,
                "win_rate": win_rate,
                "closed_count": closed_count,
            }
        ),
        "computed_observations": observations,
    }


def _generate_sales_pipeline_report(db, org_id, user_id, arguments: dict):
    period = _require_period(arguments)
    if isinstance(period, dict):
        return period
    start, end = _period_bounds(period)

    data = _gather_pipeline_data(db, org_id, start, end, period)

    llm = None
    try:
        raw = model_router.complete(
            _narrative_messages("sales pipeline", data), temperature=0.2
        )
        llm = _parse_llm_json(raw)
    except Exception:  # noqa: BLE001 - rate limit / no key -> data-only fallback
        llm = None

    narrative, observations, source = _merge_insights(data, llm)
    return {
        "report": "sales_pipeline",
        "period": period,
        "open_pipeline_value": data["open_pipeline_value"],
        "won_value": data["won_value"],
        "won_count": data["won_count"],
        "lost_count": data["lost_count"],
        "win_rate": data["win_rate"],
        "stage_distribution": data["stage_distribution"],
        "narrative": narrative,
        "observations": observations,
        "source": source,
    }


# ------------------------------------------------------------ productivity

_TASK_DONE = {"done", "completed"}


def _employee_name(emp) -> str:
    name = f"{emp.first_name or ''} {emp.last_name or ''}".strip()
    return name or emp.employee_code or "Unnamed"


def _hours_between(start, end):
    if not start or not end:
        return None
    delta = end - start
    return round(delta.total_seconds() / 3600.0, 2)


def _computed_productivity_narrative(data: dict) -> str:
    return (
        f"Across {data['employee_count']} employee(s), the team completed "
        f"{data['team_total_tasks_completed']} task(s) and has "
        f"{data['team_total_tasks_overdue']} overdue task(s) "
        f"in {data['period'].replace('_', ' ')}."
    )


def _gather_productivity_data(db, org_id, start, end, period) -> dict:
    from datetime import datetime, timezone

    from app.models.hr import Attendance, Employee
    from app.models.task import Task

    now = datetime.now(timezone.utc)
    employees = (
        db.query(Employee).filter(Employee.organization_id == org_id).all()
    )
    tasks = db.query(Task).filter(Task.organization_id == org_id).all()
    attendance = (
        db.query(Attendance).filter(Attendance.organization_id == org_id).all()
    )

    # tasks_completed uses Task.updated_at as the "marked done" timestamp:
    # Task has no completed_at column, and updated_at is the only timestamp
    # that reflects the final status change.
    per_employee = []
    team_completed = 0
    team_overdue = 0
    completion_hours = []
    employees_with_overdue = 0

    for emp in employees:
        assigned = [t for t in tasks if t.assigned_to == emp.user_id]
        completed = [
            t
            for t in assigned
            if (t.status or "").lower() in _TASK_DONE
            and t.updated_at
            and start <= t.updated_at <= end
        ]
        overdue = [
            t
            for t in assigned
            if (t.status or "").lower() not in _TASK_DONE
            and t.due_date
            and t.due_date < now
        ]
        hours = [_hours_between(t.created_at, t.updated_at) for t in completed]
        hours = [h for h in hours if h is not None]
        avg_completion = round(sum(hours) / len(hours), 2) if hours else None

        presence_rows = [
            a
            for a in attendance
            if a.employee_id == emp.id and a.check_in and start <= a.check_in <= end
        ]
        days_present = len({a.check_in.date() for a in presence_rows})

        team_completed += len(completed)
        team_overdue += len(overdue)
        completion_hours.extend(hours)
        if overdue:
            employees_with_overdue += 1

        per_employee.append(
            {
                "employee_id": str(emp.id),
                "name": _employee_name(emp),
                "tasks_completed": len(completed),
                "tasks_overdue": len(overdue),
                "avg_completion_hours": avg_completion,
                "days_present": days_present,
            }
        )

    per_employee.sort(
        key=lambda e: (e["tasks_completed"], e["name"]), reverse=True
    )
    top_employees = per_employee[:_TOP_LIMIT]

    team_avg_completion = (
        round(sum(completion_hours) / len(completion_hours), 2)
        if completion_hours
        else None
    )

    flags = []
    if employees_with_overdue:
        flags.append(f"{employees_with_overdue} employee(s) have overdue tasks.")
    if team_completed == 0:
        flags.append("No tasks were completed in the period.")
    if not any(p["days_present"] for p in per_employee):
        flags.append("No attendance recorded in the period.")

    observations = list(flags)
    for emp in top_employees[0:1]:
        if emp["tasks_completed"]:
            observations.append(
                f"{emp['name']} led with {emp['tasks_completed']} task(s) completed."
            )
    observations = observations[:3]

    return {
        "period": period,
        "total_employees": len(employees),
        "team_total_tasks_completed": team_completed,
        "team_total_tasks_overdue": team_overdue,
        "team_avg_completion_hours": team_avg_completion,
        "per_employee": top_employees,
        "flags": flags,
        "computed_narrative": _computed_productivity_narrative(
            {
                "period": period,
                "employee_count": len(employees),
                "team_total_tasks_completed": team_completed,
                "team_total_tasks_overdue": team_overdue,
            }
        ),
        "computed_observations": observations,
    }


def _generate_productivity_report(db, org_id, user_id, arguments: dict):
    period = _require_period(arguments)
    if isinstance(period, dict):
        return period
    start, end = _period_bounds(period)

    data = _gather_productivity_data(db, org_id, start, end, period)

    llm = None
    try:
        raw = model_router.complete(
            _narrative_messages("productivity", data), temperature=0.2
        )
        llm = _parse_llm_json(raw)
    except Exception:  # noqa: BLE001 - rate limit / no key -> data-only fallback
        llm = None

    narrative, observations, source = _merge_insights(data, llm)
    return {
        "report": "productivity",
        "period": period,
        "team_total_tasks_completed": data["team_total_tasks_completed"],
        "team_total_tasks_overdue": data["team_total_tasks_overdue"],
        "team_avg_completion_hours": data["team_avg_completion_hours"],
        "per_employee": data["per_employee"],
        "narrative": narrative,
        "observations": observations,
        "source": source,
    }


# --------------------------------------------------------------- forecasting


def _forecast_spans(period):
    """Return (end, span) for a reference period so we can build comparable
    historical windows of equal length. ``end`` is the exclusive end of the
    most recent reference period."""
    now = datetime.now(timezone.utc)
    today = now.date()
    if period == "last_7_days":
        return now, timedelta(days=7)
    if period == "last_30_days":
        return now, timedelta(days=30)
    if period == "month_to_date":
        days_in_month = (date(today.year, today.month, 1) + relativedelta(months=1, days=-1)).day
        return now, timedelta(days=days_in_month)
    if period == "last_quarter":
        current_q_start = datetime.combine(
            _quarter_start(today), time.min, tzinfo=timezone.utc
        )
        end = current_q_start
        span = end - (end - relativedelta(months=3))
        return end, span
    if period == "last_year":
        end = datetime.combine(date(today.year, 1, 1), time.min, tzinfo=timezone.utc)
        return end, timedelta(days=365)
    return None, None


def _computed_forecast_narrative(data: dict) -> str:
    return (
        f"Revenue is projected at ${data['projected_revenue']:.2f} for the "
        f"next period based on a 3-period moving average of the historical "
        f"periods (${data['revenues'][0]['revenue']:.2f}, "
        f"${data['revenues'][1]['revenue']:.2f}, "
        f"${data['revenues'][2]['revenue']:.2f})."
    )


def _generate_forecast_report(db, org_id, user_id, arguments: dict):
    period = _require_period(arguments)
    if isinstance(period, dict):
        return period
    end, span = _forecast_spans(period)
    if end is None:
        return {"error": f"invalid period '{period}'"}

    periods = [
        ("period_1_oldest", end - 3 * span, end - 2 * span),
        ("period_2_middle", end - 2 * span, end - 1 * span),
        ("period_3_most_recent", end - 1 * span, end),
    ]
    revenues = []
    for label, s, e in periods:
        rev = _gather_revenue_data(db, org_id, s, e, "forecast")["total_revenue"]
        revenues.append(
            {
                "label": label,
                "start": s.isoformat(),
                "end": e.isoformat(),
                "revenue": rev,
            }
        )

    projected = round(
        (revenues[0]["revenue"] + revenues[1]["revenue"] + revenues[2]["revenue"]) / 3,
        2,
    )
    next_start = end
    next_end = end + span

    observations = []
    most_recent = revenues[2]["revenue"]
    observations.append(f"Most recent period revenue: ${most_recent:.2f}.")
    peak = max(r["revenue"] for r in revenues)
    observations.append(f"Highest historical period revenue: ${peak:.2f}.")

    data = {
        "period": period,
        "method": "3-period moving average",
        "historical_revenues": revenues,
        "projected_revenue": projected,
        "projected_period_start": next_start.isoformat(),
        "projected_period_end": next_end.isoformat(),
        "computed_narrative": _computed_forecast_narrative(
            {"projected_revenue": projected, "revenues": revenues}
        ),
        "computed_observations": observations,
    }

    llm = None
    try:
        raw = model_router.complete(
            _narrative_messages("forecast", data), temperature=0.2
        )
        llm = _parse_llm_json(raw)
    except Exception:  # noqa: BLE001 - rate limit / LLM failure -> keep numbers
        llm = None

    narrative, obs, source = _merge_insights(data, llm)
    return {
        "report": "forecast",
        "period": period,
        "method": data["method"],
        "historical_revenues": revenues,
        "projected_revenue": projected,
        "projected_next_period": {
            "start": next_start.isoformat(),
            "end": next_end.isoformat(),
        },
        "narrative": narrative,
        "observations": obs,
        "source": source,
    }


# ---------------------------------------------------------------- cohorts


def _computed_cohort_narrative(data: dict) -> str:
    return (
        f"In {data['period'].replace('_', ' ')}, {data['new_customers_acquired']} "
        f"new customer(s) were acquired; {data['engaged_customers']} of "
        f"{data['active_customers']} active customer(s) showed engagement."
    )


def _gather_cohort_data(db, org_id, start, end, period) -> dict:
    from app.models.activity import Activity
    from app.models.customer import Customer
    from app.models.invoice import Invoice

    all_customers = (
        db.query(Customer)
        .filter(Customer.organization_id == org_id)
        .all()
    )
    cust_ids = {c.id for c in all_customers}

    acquired = [c for c in all_customers if c.created_at and start <= c.created_at <= end]
    acquired_count = len(acquired)

    active_customers = [c for c in all_customers if (c.status or "").lower() == "active"]
    active_count = len(active_customers)
    active_ids = {c.id for c in active_customers}

    # engaged = an activity OR invoice recorded against the customer in period.
    current_activity_ids = {
        a.entity_id
        for a in db.query(Activity)
        .filter(
            Activity.organization_id == org_id,
            Activity.created_at >= start,
            Activity.created_at <= end,
        )
        .all()
    } & cust_ids
    engaged_ids = current_activity_ids | {
        i.customer_id
        for i in db.query(Invoice)
        .filter(
            Invoice.organization_id == org_id,
            Invoice.created_at >= start,
            Invoice.created_at <= end,
        )
        .all()
        if i.customer_id
    }
    engaged_ids = engaged_ids & cust_ids
    engaged_count = sum(1 for cid in active_ids if cid in engaged_ids)

    # churn signal: active customer with activity in the prior period but none
    # in the current period (activity only, matching the definition).
    prior_span = end - start
    prior_start = start - prior_span
    prior_activity_ids = {
        a.entity_id
        for a in db.query(Activity)
        .filter(
            Activity.organization_id == org_id,
            Activity.created_at >= prior_start,
            Activity.created_at < start,
        )
        .all()
    } & cust_ids
    churn_count = sum(
        1 for cid in active_ids if cid in prior_activity_ids and cid not in engaged_ids
    )

    flags = []
    if churn_count:
        flags.append(f"{churn_count} active customer(s) lost engagement in the period.")
    if acquired_count == 0:
        flags.append("No new customers acquired in the period.")

    observations = [
        f"{acquired_count} new customer(s) acquired, "
        f"{engaged_count} engaged in the period."
    ]
    observations = list(flags) + observations
    observations = observations[:3]

    return {
        "period": period,
        "new_customers_acquired": acquired_count,
        "active_customers": active_count,
        "engaged_customers": engaged_count,
        "churn_candidates": churn_count,
        # No segment column exists on Customer, so segmentation is skipped.
        "segmentation": None,
        "segmentation_note": (
            "Customer has no segment column; revenue segmentation skipped."
        ),
        "flags": flags,
        "computed_narrative": _computed_cohort_narrative(
            {
                "period": period,
                "new_customers_acquired": acquired_count,
                "active_customers": active_count,
                "engaged_customers": engaged_count,
            }
        ),
        "computed_observations": observations,
    }


def _generate_customer_cohort_report(db, org_id, user_id, arguments: dict):
    period = _require_period(arguments)
    if isinstance(period, dict):
        return period
    start, end = _period_bounds(period)

    data = _gather_cohort_data(db, org_id, start, end, period)

    llm = None
    try:
        raw = model_router.complete(
            _narrative_messages("customer cohort", data), temperature=0.2
        )
        llm = _parse_llm_json(raw)
    except Exception:  # noqa: BLE001 - rate limit / LLM failure -> keep numbers
        llm = None

    narrative, observations, source = _merge_insights(data, llm)
    return {
        "report": "customer_cohort",
        "period": period,
        "new_customers_acquired": data["new_customers_acquired"],
        "active_customers": data["active_customers"],
        "engaged_customers": data["engaged_customers"],
        "churn_candidates": data["churn_candidates"],
        "segmentation": data["segmentation"],
        "segmentation_note": data["segmentation_note"],
        "narrative": narrative,
        "observations": observations,
        "source": source,
    }


REPORTING_TOOLS: dict[str, ToolSpec] = {
    "generate_revenue_report": ToolSpec(
        name="generate_revenue_report",
        description=(
            "Generate a revenue report for a period, computing real "
            "aggregates from paid invoices (total, count, average, top "
            "customers) with AI narrative commentary."
        ),
        parameters={
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": sorted(_PERIODS),
                },
            },
            "required": ["period"],
        },
        handler=_generate_revenue_report,
    ),
    "generate_expense_report": ToolSpec(
        name="generate_expense_report",
        description=(
            "Generate an expense report for a period, computing real "
            "aggregates from expenses (total, count, by category, top "
            "expenses) with AI narrative commentary."
        ),
        parameters={
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": sorted(_PERIODS),
                },
            },
            "required": ["period"],
        },
        handler=_generate_expense_report,
    ),
    "generate_sales_pipeline_report": ToolSpec(
        name="generate_sales_pipeline_report",
        description=(
            "Generate a sales pipeline report for a period, computing real "
            "aggregates from deals (open pipeline value, won/lost, win rate, "
            "stage distribution) with AI narrative commentary."
        ),
        parameters={
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": sorted(_PERIODS),
                },
            },
            "required": ["period"],
        },
        handler=_generate_sales_pipeline_report,
    ),
    "generate_productivity_report": ToolSpec(
        name="generate_productivity_report",
        description=(
            "Generate an employee productivity report for a period, computing "
            "real per-employee aggregate (tasks completed, tasks overdue, "
            "average completion time, attendance days present) with AI "
            "narrative commentary."
        ),
        parameters={
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": sorted(_PERIODS),
                },
            },
            "required": ["period"],
        },
        handler=_generate_productivity_report,
    ),
    "generate_forecast_report": ToolSpec(
        name="generate_forecast_report",
        description=(
            "Forecast next-period revenue using a simple, stated 3-period "
            "moving average over historical revenue; returns the actual "
            "historical numbers used plus the projection."
        ),
        parameters={
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": sorted(_PERIODS),
                },
            },
            "required": ["period"],
        },
        handler=_generate_forecast_report,
    ),
    "generate_customer_cohort_report": ToolSpec(
        name="generate_customer_cohort_report",
        description=(
            "Aggregate cohort analytics: new customers acquired, active "
            "customer count, engaged-in-period customers and a churn-like "
            "signal, with AI narrative commentary."
        ),
        parameters={
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": sorted(_PERIODS),
                },
            },
            "required": ["period"],
        },
        handler=_generate_customer_cohort_report,
    ),
}
