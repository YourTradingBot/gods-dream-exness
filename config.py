import json
import os
from typing import Dict, Any

class Config:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance
    
    def load_config(self):
        """Load configuration from secrets.json"""
        try:
            with open('secrets.json', 'r') as f:
                self._config = json.load(f)
            print("✅ Configuration loaded from secrets.json")
        except FileNotFoundError:
            # Create default config
            self._config = self.get_default_config()
            self.save_config()
            print("⚠️ Created default secrets.json. Please edit it!")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "telegram": {
                "api_id": "YOUR_API_ID_HERE",
                "api_hash": "YOUR_API_HASH_HERE",
                "phone": "+1234567890",
                "bot_token": "YOUR_BOT_TOKEN_HERE",
                "chat_id": "YOUR_CHAT_ID_HERE"
            },
            "channels": {
                "A": {
                    "name": "KJF Signals",
                    "source": "@KJFSignals",
                    "enabled": True
                },
                "B": {
                    "name": "Fortune Skool",
                    "source": "@FortuneSkool",
                    "enabled": True
                }
            },
            "trading": {
                "account_balance": 1000.00,
                "account_currency": "USD",
                "risk_percentage": 1.0,
                "broker": "Exness",
                "update_interval": 20,
                "balance_report_hours": 1
            },
            "system": {
                "environment": "production",
                "log_level": "INFO",
                "self_ping_interval": 240
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        with open('secrets.json', 'w') as f:
            json.dump(self._config, f, indent=2)
    
    @property
    def telegram(self) -> Dict[str, Any]:
        return self._config.get("telegram", {})
    
    @property
    def channels(self) -> Dict[str, Any]:
        return self._config.get("channels", {})
    
    @property
    def trading(self) -> Dict[str, Any]:
        return self._config.get("trading", {})
    
    @property
    def system(self) -> Dict[str, Any]:
        return self._config.get("system", {})
    
    def update(self, section: str, key: str, value: Any):
        """Update configuration"""
        if section in self._config and key in self._config[section]:
            self._config[section][key] = value
            self.save_config()

config = Config()
