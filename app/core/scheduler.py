from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.scrape_service import fetch_stock_data
from app.services.trade_service import execute_trade
from app.services.test_trade_service import execute_test_trade
import logging
from pytz import timezone

# Define the timezone
ASIA_KOLKATA = timezone("Asia/Kolkata")

# Initialize the scheduler
scheduler = AsyncIOScheduler(timezone=ASIA_KOLKATA)


async def schedule_async_task(task_func, *args):
    try:
        await task_func(*args)
    except Exception as e:
        logging.error(f"Error in scheduled task: {e}")


def setup_scheduled_tasks(scheduler):
    fetch_stock_trigger = CronTrigger(
        second=0, minute=59, hour=23, day="*", month="*", day_of_week="0-6", timezone=ASIA_KOLKATA
    )
    buy_trigger = CronTrigger(
        second=5, minute=16, hour=15, day="*", month="*", day_of_week="0-4", timezone=ASIA_KOLKATA
    )
    sell_trigger = CronTrigger(
        second=5, minute=16, hour=9, day="*", month="*", day_of_week="0-4", timezone=ASIA_KOLKATA
    )
    test_buy_trigger = CronTrigger(
        second=5, minute=16, hour=15, day="*", month="*", day_of_week="0-4", timezone=ASIA_KOLKATA
    )
    test_sell_trigger = CronTrigger(
        second=5, minute=16, hour=9, day="*", month="*", day_of_week="0-4", timezone=ASIA_KOLKATA
    )

    scheduler.add_job(schedule_async_task, fetch_stock_trigger, args=[fetch_stock_data])
    # scheduler.add_job(schedule_async_task, buy_trigger, args=[execute_trade, "buy"])
    # scheduler.add_job(schedule_async_task, sell_trigger, args=[execute_trade, "sell"])
    scheduler.add_job(schedule_async_task, test_buy_trigger, args=[execute_test_trade, "buy"])
    scheduler.add_job(schedule_async_task, test_sell_trigger, args=[execute_test_trade, "sell"])

