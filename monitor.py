import asyncio
import logging
from telethon import TelegramClient, events
from datetime import datetime
from config import config
from database import db
from trading import TradingEngine

logger = logging.getLogger(__name__)

class ChannelMonitor:
    def __init__(self):
        self.telegram_config = config.telegram
        self.channels_config = config.channels
        self.trading_engine = TradingEngine()
        
        # Initialize Telethon client
        self.client = TelegramClient(
            'gods_dream_session',
            self.telegram_config['api_id'],
            self.telegram_config['api_hash']
        )
        
        self.channel_entities = {}
        self.signal_counters = {'A': 0, 'B': 0}
    
    async def start(self):
        """Start monitoring channels"""
        logger.info("🔍 Starting channel monitor...")
        
        try:
            # Connect to Telegram
            await self.client.start(phone=self.telegram_config['phone'])
            logger.info("✅ Connected to Telegram")
            
            # Get channel entities
            await self._get_channel_entities()
            
            # Setup event handlers
            self._setup_handlers()
            
            # Start monitoring
            logger.info("👂 Listening for signals...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Channel monitor error: {e}")
    
    async def _get_channel_entities(self):
        """Get channel entities from Telegram"""
        for channel_id, channel_info in self.channels_config.items():
            if channel_info.get('enabled', True):
                source = channel_info['source']
                try:
                    entity = await self.client.get_entity(source)
                    self.channel_entities[channel_id] = entity
                    logger.info(f"✅ Connected to {channel_info['name']}")
                except Exception as e:
                    logger.error(f"❌ Failed to connect to {channel_info['name']}: {e}")
    
    def _setup_handlers(self):
        """Setup Telethon event handlers"""
        
        @self.client.on(events.NewMessage(chats=list(self.channel_entities.values())))
        async def handler(event):
            """Handle new messages from monitored channels"""
            try:
                # Determine which channel
                channel_id = None
                for cid, entity in self.channel_entities.items():
                    if event.chat_id == entity.id:
                        channel_id = cid
                        break
                
                if not channel_id:
                    return
                
                # Get message text
                message_text = event.message.text or ""
                
                # Check if message contains trading signal
                if self._is_trading_signal(message_text):
                    logger.info(f"📡 Signal from Channel {channel_id}: {message_text[:100]}...")
                    
                    # Save signal to database
                    db.save_signal(channel_id, message_text)
                    
                    # Process signal
                    await self._process_signal(channel_id, message_text)
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
        
        # Also handle images (for image-based signals)
        @self.client.on(events.NewMessage(chats=list(self.channel_entities.values())))
        async def image_handler(event):
            if event.message.photo:
                # For image signals, we would extract text using OCR
                # For now, just log
                logger.info(f"📸 Image signal received")
    
    def _is_trading_signal(self, text: str) -> bool:
        """Check if text contains trading signal"""
        text = text.upper()
        
        # Check for trading keywords
        keywords = ['BUY', 'SELL', 'LONG', 'SHORT', 'ENTRY', 'SL', 'TP', 
                   'STOP LOSS', 'TAKE PROFIT', 'EURUSD', 'GBPUSD', 'XAUUSD']
        
        return any(keyword in text for keyword in keywords)
    
    async def _process_signal(self, channel_id: str, message_text: str):
        """Process trading signal"""
        try:
            # Parse signal
            signal_data = self.trading_engine.parse_signal(message_text)
            
            if not signal_data:
                logger.warning(f"Could not parse signal from Channel {channel_id}")
                return
            
            # Update channel
            signal_data['channel'] = channel_id
            
            # Get next signal number
            self.signal_counters[channel_id] += 1
            
            # Generate trade ID
            trade_id = self.trading_engine.generate_trade_id(
                channel_id, self.signal_counters[channel_id]
            )
            
            # Get account details from config
            account_balance = config.trading['account_balance']
            account_currency = config.trading['account_currency']
            risk_percent = config.trading['risk_percentage']
            
            # Calculate lot size
            lot_size = self.trading_engine.calculate_lot_size(
                balance=account_balance,
                risk_percent=risk_percent,
                entry=signal_data['entry'],
                sl=signal_data['sl'],
                symbol=signal_data['symbol'],
                account_currency=account_currency
            )
            
            # Prepare trade data
            trade_data = {
                'trade_id': trade_id,
                'channel': channel_id,
                'symbol': signal_data['symbol'],
                'action': signal_data['action'],
                'entry_price': signal_data['entry'],
                'sl_price': signal_data['sl'],
                'tp1_price': signal_data.get('tp1', 0),
                'tp2_price': signal_data.get('tp2', 0),
                'lot_size': lot_size,
                'account_currency': account_currency,
                'account_balance': account_balance,
                'risk_percent': risk_percent
            }
            
            # Save to database
            trade_db_id = db.save_trade(trade_data)
            
            # Send notification via Telegram bot
            from bot import send_trade_setup
            await send_trade_setup(trade_data)
            
            logger.info(f"✅ Trade setup created: {trade_id}")
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")

# Global monitor instance
monitor = ChannelMonitor()
