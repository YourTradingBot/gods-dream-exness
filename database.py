import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('data/trading.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE,
                channel TEXT,
                symbol TEXT,
                action TEXT,
                entry_price REAL,
                sl_price REAL,
                tp1_price REAL,
                tp2_price REAL,
                lot_size REAL,
                account_currency TEXT,
                account_balance REAL,
                risk_percent REAL,
                status TEXT DEFAULT 'pending',
                profit_pips REAL DEFAULT 0,
                profit_amount REAL DEFAULT 0,
                opened_at TIMESTAMP,
                tp1_hit_at TIMESTAMP,
                closed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT,
                message TEXT,
                parsed_data TEXT,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                channel TEXT,
                trades_taken INTEGER DEFAULT 0,
                trades_won INTEGER DEFAULT 0,
                total_pips REAL DEFAULT 0,
                total_profit REAL DEFAULT 0,
                win_rate REAL DEFAULT 0
            )
        ''')
        
        self.conn.commit()
    
    def save_trade(self, trade_data: Dict) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO trades (
                trade_id, channel, symbol, action, entry_price, sl_price,
                tp1_price, tp2_price, lot_size, account_currency,
                account_balance, risk_percent, status, opened_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data['trade_id'],
            trade_data['channel'],
            trade_data['symbol'],
            trade_data['action'],
            trade_data['entry_price'],
            trade_data['sl_price'],
            trade_data['tp1_price'],
            trade_data['tp2_price'],
            trade_data['lot_size'],
            trade_data['account_currency'],
            trade_data['account_balance'],
            trade_data['risk_percent'],
            'open',
            datetime.now()
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_trade(self, trade_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE trade_id = ?", (trade_id,))
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def update_trade_status(self, trade_id: str, status: str):
        cursor = self.conn.cursor()
        
        if status == 'tp1_hit':
            cursor.execute('''
                UPDATE trades 
                SET status = ?, tp1_hit_at = ?, tp2_price = entry_price
                WHERE trade_id = ?
            ''', (status, datetime.now(), trade_id))
        elif status == 'closed':
            cursor.execute('''
                UPDATE trades 
                SET status = ?, closed_at = ?
                WHERE trade_id = ?
            ''', (status, datetime.now(), trade_id))
        else:
            cursor.execute('''
                UPDATE trades 
                SET status = ?
                WHERE trade_id = ?
            ''', (status, trade_id))
        
        self.conn.commit()
    
    def update_trade_profit(self, trade_id: str, profit_pips: float, profit_amount: float):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE trades 
            SET profit_pips = ?, profit_amount = ?
            WHERE trade_id = ?
        ''', (profit_pips, profit_amount, trade_id))
        self.conn.commit()
    
    def get_active_trades(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE status IN ('open', 'tp1_hit')")
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def save_signal(self, channel: str, message: str, parsed_data: Dict = None):
        cursor = self.conn.cursor()
        parsed_json = json.dumps(parsed_data) if parsed_data else None
        cursor.execute('''
            INSERT INTO signals (channel, message, parsed_data)
            VALUES (?, ?, ?)
        ''', (channel, message, parsed_json))
        self.conn.commit()
    
    def record_performance(self, channel: str, date: datetime, 
                          trades_taken: int, trades_won: int,
                          total_pips: float, total_profit: float):
        cursor = self.conn.cursor()
        
        win_rate = (trades_won / trades_taken * 100) if trades_taken > 0 else 0
        
        cursor.execute('''
            INSERT INTO performance (date, channel, trades_taken, trades_won, 
                                   total_pips, total_profit, win_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date.date(), channel, trades_taken, trades_won, 
              total_pips, total_profit, win_rate))
        self.conn.commit()

db = Database()
