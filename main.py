import asyncio
import logging
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os

from config import config
from monitor import monitor
from keep_alive import keep_alive
from bot import bot
import database

# Setup logging
logging.basicConfig(
    level=config.system.get('log_level', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Store active tasks
active_tasks = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting God's Dream Trading System...")
    logger.info(f"💰 Account Balance: ${config.trading['account_balance']:,.2f}")
    logger.info(f"📊 Risk Percentage: {config.trading['risk_percentage']}%")
    
    try:
        # Start 24/7 system
        keep_alive_task = asyncio.create_task(keep_alive.start())
        active_tasks.append(keep_alive_task)
        logger.info("✅ 24/7 system started")
        
        # Start Telegram bot
        bot_task = asyncio.create_task(bot.start())
        active_tasks.append(bot_task)
        logger.info("✅ Telegram bot started")
        
        # Start channel monitor
        monitor_task = asyncio.create_task(monitor.start())
        active_tasks.append(monitor_task)
        logger.info("✅ Channel monitor started")
        
        logger.info("✅ All systems started successfully!")
        
        yield  # App runs here
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
        
    finally:
        # Shutdown
        logger.info("🛑 Shutting down...")
        keep_alive.is_running = False
        
        for task in active_tasks:
            task.cancel()
        
        logger.info("✅ Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="God's Dream Trading System",
    description="24/7 Automated Trading Bot",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root endpoint"""
    from datetime import datetime
    return {
        "message": "God's Dream Trading Bot",
        "status": "running",
        "version": "1.0.0",
        "uptime": str(datetime.now() - keep_alive.start_time).split('.')[0],
        "account_balance": f"${config.trading['account_balance']:,.2f}"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "telegram_bot": "running",
            "channel_monitor": "running",
            "24_7_system": "running",
            "database": "connected"
        }
    }

@app.get("/status")
async def status():
    """System status"""
    from database import db
    active_trades = db.get_active_trades()
    
    return {
        "system": {
            "uptime": str(datetime.now() - keep_alive.start_time).split('.')[0],
            "ping_count": keep_alive.ping_count,
            "environment": config.system['environment']
        },
        "trading": {
            "account_balance": config.trading['account_balance'],
            "account_currency": config.trading['account_currency'],
            "risk_percentage": config.trading['risk_percentage'],
            "active_trades": len(active_trades)
        },
        "channels": {
            "A": config.channels['A']['name'],
            "B": config.channels['B']['name']
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
