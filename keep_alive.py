import asyncio
import aiohttp
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class KeepAliveSystem:
    def __init__(self):
        self.is_running = False
        self.base_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:10000")
        self.ping_count = 0
        self.start_time = datetime.now()
    
    async def start(self):
        """Start 24/7 keep-alive system"""
        self.is_running = True
        logger.info("🔔 Starting 24/7 keep-alive system")
        
        # Start multiple strategies
        tasks = [
            self._self_ping(),
            self._background_tasks(),
            self._health_monitoring()
        ]
        
        await asyncio.gather(*tasks)
    
    async def _self_ping(self):
        """Self-ping to keep Render awake"""
        while self.is_running:
            try:
                await self._ping_endpoint("/health")
                self.ping_count += 1
                logger.debug(f"✅ Self-ping #{self.ping_count} successful")
            except Exception as e:
                logger.warning(f"⚠️ Self-ping failed: {e}")
            
            # Ping every 4 minutes (less than Render's 15-minute sleep)
            await asyncio.sleep(240)
    
    async def _ping_endpoint(self, endpoint: str):
        """Ping a specific endpoint"""
        url = f"{self.base_url}{endpoint}"
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Endpoint returned {response.status}")
                return True
    
    async def _background_tasks(self):
        """Run background tasks to keep system active"""
        while self.is_running:
            # Do some background work
            await asyncio.sleep(60)
    
    async def _health_monitoring(self):
        """Monitor system health"""
        while self.is_running:
            # Log uptime
            uptime = datetime.now() - self.start_time
            hours, remainder = divmod(uptime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            logger.info(f"⏰ System uptime: {int(hours)}h {int(minutes)}m {int(seconds)}s")
            logger.info(f"📊 Total pings: {self.ping_count}")
            
            await asyncio.sleep(300)  # Log every 5 minutes

keep_alive = KeepAliveSystem()
