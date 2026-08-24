import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import SessionLocal
from models import AdminSetting
from services.email_service import send_restock_email


logger = logging.getLogger(__name__)
CHINA_TZ = ZoneInfo("Asia/Shanghai")


def _scheduled_report_job():
    db = SessionLocal()
    try:
        schedule = os.getenv("REPORT_SCHEDULE", "disabled").lower()
        today = datetime.now(CHINA_TZ).date().isoformat()
        delivery_key = f"{schedule}:{today}"
        setting = db.query(AdminSetting).filter(AdminSetting.key == "last_report_schedule_key").first()
        if setting and setting.value == delivery_key:
            return
        result = send_restock_email(db)
        if result.get("ok"):
            if setting:
                setting.value = delivery_key
            else:
                db.add(AdminSetting(key="last_report_schedule_key", value=delivery_key))
            db.commit()
            logger.info("scheduled restock report sent: %s", delivery_key)
        else:
            logger.error("scheduled restock report failed: %s", result.get("msg"))
    except Exception:
        logger.exception("scheduled restock report crashed")
        db.rollback()
    finally:
        db.close()


def create_scheduler():
    schedule = os.getenv("REPORT_SCHEDULE", "disabled").lower()
    if schedule == "disabled":
        return None
    hour = max(0, min(23, int(os.getenv("REPORT_SCHEDULE_HOUR", "8"))))
    trigger_options = {
        "daily": {"hour": hour, "minute": 0},
        "weekly": {"day_of_week": "mon", "hour": hour, "minute": 0},
        "semimonthly": {"day": "1,15", "hour": hour, "minute": 0},
        "monthly": {"day": "1", "hour": hour, "minute": 0},
    }
    if schedule not in trigger_options:
        raise RuntimeError(f"不支持的 REPORT_SCHEDULE: {schedule}")
    scheduler = BackgroundScheduler(timezone=CHINA_TZ)
    scheduler.add_job(
        _scheduled_report_job,
        CronTrigger(timezone=CHINA_TZ, **trigger_options[schedule]),
        id="restock_report",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler

