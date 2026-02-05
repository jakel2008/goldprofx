
import MetaTrader5 as mt5
import json
import os
import time
import logging
from datetime import datetime

# Try to import dotenv and load environment variables
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv is not installed. Install it with: pip install python-dotenv")

ACCOUNT_NUMBER = int(os.getenv("MT5_ACCOUNT"))
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")
PATH = os.getenv("MT5_PATH")

# إعدادات التداول
LOT_SIZE = 0.1
MAX_SLIPPAGE = 3
MAGIC_NUMBER = 2024

# إعدادات المجلدات
SIGNAL_FOLDER = "signals"
EXECUTED_FOLDER = "executed_signals"
LOG_FILE = "autotrade.log"

# إعداد التسجيل
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# التأكد من وجود المجلدات
os.makedirs(SIGNAL_FOLDER, exist_ok=True)
os.makedirs(EXECUTED_FOLDER, exist_ok=True)

def connect_to_mt5():
    if not mt5.initialize(path=PATH, login=ACCOUNT_NUMBER, password=PASSWORD, server=SERVER):
        logging.error(f"Failed to initialize MT5: {mt5.last_error()}")
        return False
    if not mt5.login(login=ACCOUNT_NUMBER, password=PASSWORD, server=SERVER):
        logging.error(f"Failed to login to account: {mt5.last_error()}")
        return False
    logging.info(f"Connected to MT5 account #{ACCOUNT_NUMBER}")
    return True

def place_trade(signal):
    symbol = signal["symbol"]
    trade_type = signal["trade_type"]
    stop_loss = signal["stop_loss"]
    take_profits = signal["take_profit"]

    if not mt5.symbol_select(symbol, True):
        logging.error(f"Symbol {symbol} not available")
        return False

    info = mt5.symbol_info(symbol)
    if info is None:
        logging.error(f"Failed to get market data for {symbol}")
        return False

    price = info.ask if trade_type == "BUY" else info.bid
    order_type = mt5.ORDER_TYPE_BUY if trade_type == "BUY" else mt5.ORDER_TYPE_SELL
    volume_per_trade = LOT_SIZE / len(take_profits)

    success_count = 0

    for i, tp in enumerate(take_profits):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume_per_trade,
            "type": order_type,
            "price": price,
            "sl": stop_loss,
            "tp": tp,
            "deviation": MAX_SLIPPAGE,
            "magic": MAGIC_NUMBER + i,
            "comment": f"AutoTrade TP{i+1}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logging.error(f"Trade TP{i+1} failed: {result.comment}")
        else:
            logging.info(f"Trade TP{i+1} executed: {symbol} {trade_type} at {price}")
            success_count += 1

    return success_count > 0

def monitor_signals():
    logging.info("AutoTradeBot started. Monitoring for trading signals...")

    try:
        while True:
            signal_files = [f for f in os.listdir(SIGNAL_FOLDER) if f.endswith(".json")]

            for file in signal_files:
                filepath = os.path.join(SIGNAL_FOLDER, file)
                try:
                    with open(filepath, "r") as f:
                        signal = json.load(f)

                    logging.info(f"New signal: {signal['symbol']} {signal['trade_type']}")
                    
                    if connect_to_mt5():
                        try:
                            if place_trade(signal):
                                new_name = os.path.join(EXECUTED_FOLDER, f"executed_{file}")
                                os.rename(filepath, new_name)
                                logging.info(f"Trade executed and file moved: {new_name}")
                            else:
                                logging.warning("Trade execution failed.")
                        finally:
                            mt5.shutdown()
                    else:
                        pass
                except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
                    logging.exception(f"Error processing {file}: {e}")
                    os.rename(filepath, os.path.join(EXECUTED_FOLDER, f"error_{file}"))
                except Exception as e:
                    # Log unexpected errors separately and re-raise to avoid masking bugs.
                    logging.exception(f"Unexpected error processing {file}: {e}")
                    raise
                    logging.exception(f"Error processing {file}: {e}")
                    if os.path.exists(filepath):
                        try:
                            os.rename(filepath, os.path.join(EXECUTED_FOLDER, f"error_{file}"))
                        except FileNotFoundError:
                            logging.warning(f"File {filepath} not found when attempting to move to error folder.")
                    else:
                        logging.warning(f"File {filepath} no longer exists; cannot move to error folder.")
            time.sleep(30)

    except KeyboardInterrupt:
        logging.info("AutoTradeBot stopped by user.")

if __name__ == "__main__":
    monitor_signals()
