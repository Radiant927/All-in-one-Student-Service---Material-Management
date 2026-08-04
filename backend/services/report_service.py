from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from models import Material, InventoryBatch, InventoryItem, BorrowHistory, Warehouse


def _get_today():
    """Return today's date (date only, no time)."""
    return datetime.now().date()


def _days_ago_iso(days):
    """Return ISO datetime string for N days ago."""
    return (datetime.now() - timedelta(days=days)).isoformat()


def get_current_stock(db: Session, material_id: int) -> int:
    """Get current total stock for a material across all warehouses."""
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        return 0
    if m.has_individual_tracking:
        return db.query(InventoryItem).filter(
            InventoryItem.material_id == material_id
        ).count()
    else:
        return db.query(func.sum(InventoryBatch.quantity)).filter(
            InventoryBatch.material_id == material_id
        ).scalar() or 0


def calculate_consumption_velocity(db: Session, material_id: int, window_days: int = 30):
    """Calculate daily consumption rate from borrow history.

    Returns dict: {daily_rate, total_borrowed, total_returned, net_consumption, window_days, has_sufficient_data}
    """
    cutoff = _days_ago_iso(window_days)

    total_borrowed = db.query(func.sum(BorrowHistory.quantity)).filter(
        BorrowHistory.material_id == material_id,
        BorrowHistory.action == "borrow",
        BorrowHistory.created_at >= cutoff
    ).scalar() or 0

    total_returned = db.query(func.sum(BorrowHistory.quantity)).filter(
        BorrowHistory.material_id == material_id,
        BorrowHistory.action == "return",
        BorrowHistory.created_at >= cutoff
    ).scalar() or 0

    net_consumption = max(0, total_borrowed - total_returned)
    daily_rate = round(net_consumption / window_days, 3)

    # Need at least some data to be useful
    has_sufficient_data = total_borrowed > 0

    return {
        "daily_rate": daily_rate,
        "total_borrowed": total_borrowed,
        "total_returned": total_returned,
        "net_consumption": net_consumption,
        "window_days": window_days,
        "has_sufficient_data": has_sufficient_data,
    }


def predict_stockout(db: Session, material_id: int, window_days: int = 30):
    """Predict days until stockout for a material.

    Returns: {material_id, current_stock, daily_velocity, days_until_empty,
              status, suggested_restock_qty, data_confidence}
    """
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        return None

    current_stock = get_current_stock(db, material_id)
    velocity = calculate_consumption_velocity(db, material_id, window_days)

    daily_rate = velocity["daily_rate"]
    has_data = velocity["has_sufficient_data"]

    if not has_data or daily_rate < 0.001:
        # No meaningful consumption data
        days_until_empty = None
        status = "insufficient_data"
    else:
        days_until_empty = round(current_stock / daily_rate, 1)
        if days_until_empty <= 7:
            status = "critical"
        elif days_until_empty <= 30:
            status = "warning"
        else:
            status = "ok"

    # Suggest restock: target 60 days of supply (2 months)
    if has_data and daily_rate > 0:
        suggested_restock_qty = max(0, round(daily_rate * 60 - current_stock))
    else:
        suggested_restock_qty = 0

    return {
        "material_id": material_id,
        "name": m.name,
        "icon": m.icon,
        "spec": m.spec,
        "unit": m.unit,
        "category": m.category,
        "sub_category": m.sub_category,
        "has_individual_tracking": bool(m.has_individual_tracking),
        "low_stock_threshold": m.low_stock_threshold,
        "current_stock": current_stock,
        "daily_velocity": daily_rate,
        "total_borrowed_in_window": velocity["total_borrowed"],
        "total_returned_in_window": velocity["total_returned"],
        "net_consumption": velocity["net_consumption"],
        "window_days": window_days,
        "days_until_empty": days_until_empty,
        "status": status,
        "suggested_restock_qty": suggested_restock_qty,
        "data_confidence": "high" if has_data else "low",
    }


def generate_restock_report(db: Session, window_days: int = 30):
    """Generate a full restock suggestion report for all materials."""
    materials = db.query(Material).all()
    items = []

    for m in materials:
        pred = predict_stockout(db, m.id, window_days)
        if pred:
            items.append(pred)

    # Sort: critical first, then warning, then ok, then insufficient_data
    status_order = {"critical": 0, "warning": 1, "insufficient_data": 2, "ok": 3}

    def sort_key(item):
        order = status_order.get(item["status"], 4)
        if item["days_until_empty"] is not None:
            return (order, item["days_until_empty"])
        return (order, float("inf"))

    items.sort(key=sort_key)

    critical_count = sum(1 for i in items if i["status"] == "critical")
    warning_count = sum(1 for i in items if i["status"] == "warning")
    insufficient_count = sum(1 for i in items if i["status"] == "insufficient_data")

    return {
        "generated_at": datetime.now().isoformat(),
        "window_days": window_days,
        "items": items,
        "summary": {
            "total_items": len(items),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "insufficient_data_count": insufficient_count,
        },
    }


def get_consumption_trend(db: Session, material_id: int, months: int = 3):
    """Get monthly consumption trend for a material.

    Returns list of {month, consumed} for the last `months` months.
    """
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        return None

    today = _get_today()
    trend_data = []
    total_consumed = 0

    for i in range(months - 1, -1, -1):
        # Calculate month boundaries
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)

        borrowed = db.query(func.sum(BorrowHistory.quantity)).filter(
            BorrowHistory.material_id == material_id,
            BorrowHistory.action == "borrow",
            BorrowHistory.created_at >= month_start.isoformat(),
            BorrowHistory.created_at < month_end.isoformat()
        ).scalar() or 0

        returned = db.query(func.sum(BorrowHistory.quantity)).filter(
            BorrowHistory.material_id == material_id,
            BorrowHistory.action == "return",
            BorrowHistory.created_at >= month_start.isoformat(),
            BorrowHistory.created_at < month_end.isoformat()
        ).scalar() or 0

        consumed = max(0, borrowed - returned)
        total_consumed += consumed

        trend_data.append({
            "month": f"{year}-{str(month).zfill(2)}",
            "borrowed": borrowed,
            "returned": returned,
            "consumed": consumed,
        })

    return {
        "material_id": material_id,
        "name": m.name,
        "icon": m.icon,
        "unit": m.unit,
        "data": trend_data,
        "average_monthly": round(total_consumed / months, 1) if months > 0 else 0,
        "total_consumed": total_consumed,
    }


def get_dashboard_alerts(db: Session, window_days: int = 30):
    """Get dashboard alert summary with top urgent items."""
    report = generate_restock_report(db, window_days)
    top_alerts = [i for i in report["items"] if i["status"] in ("critical", "warning")][:5]
    return {
        "critical_count": report["summary"]["critical_count"],
        "warning_count": report["summary"]["warning_count"],
        "insufficient_data_count": report["summary"]["insufficient_data_count"],
        "top_alerts": top_alerts,
    }
