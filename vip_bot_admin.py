#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unified VIP Bot - With Admin Controls
بوت موحد مع أوامر إدارية للتحكم بالمستخدمين والأدمن
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

# Encoding fix for Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

from vip_subscription_system import SubscriptionManager
from admin_panel import AdminPanel

# Settings
BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Database & Admin
subscription_manager = SubscriptionManager()
admin_panel = AdminPanel()

# Update tracking
LAST_UPDATE_FILE = "last_update.json"
ADMIN_COMMANDS = {}  # Track admin command states

def log_msg(msg):
    """Simple logging"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def is_admin(user_id):
    """Check if user is admin"""
    return admin_panel.is_admin(user_id)


def load_last_update():
    """Load last update ID"""
    try:
        if os.path.exists(LAST_UPDATE_FILE):
            with open(LAST_UPDATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_update_id', 0)
    except:
        pass
    return 0


def save_last_update(update_id):
    """Save last update ID"""
    try:
        with open(LAST_UPDATE_FILE, 'w') as f:
            json.dump({'last_update_id': update_id}, f)
    except Exception as e:
        log_msg(f"[ERROR] Save update: {e}")


def send_message(chat_id, text):
    """Send message to user"""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json().get('ok', False)
    except Exception as e:
        log_msg(f"[ERROR] Send: {e}")
        return False


def get_help_message(user_id):
    """Get help message based on user role"""
    
    user_msg = """
<b>Available Commands:</b>

/start - Welcome message
/subscribe - Get free account
/status - Check your plan
/plans - View premium plans
/referral - Get referral link

<b>Support:</b>
Write /start for help
"""
    
    admin_msg = """
<b>User Commands:</b>
/start - Welcome
/subscribe - Get free account
/status - Check plan
/plans - View plans
/referral - Referral link

<b>Admin Commands:</b>
/add_user - Add new user
/make_admin - Enable admin
/admin_list - Show admins
/users_list - Show all users
/upgrade - Upgrade subscription
/remove_admin - Remove admin
/delete_user - Delete user
/user_info - Get user info

<b>Support:</b>
Type /start for help
"""
    
    if is_admin(user_id):
        return admin_msg
    return user_msg


def add_user_admin(chat_id, user_id_str, username, first_name):
    """Add user from admin command"""
    try:
        user_id = int(user_id_str)
        success, msg = subscription_manager.add_user(user_id, username, first_name)
        
        if success:
            response = f"[OK] User added!\n\n{msg}"
        else:
            response = f"[ERROR] {msg}"
    except ValueError:
        response = "[ERROR] Invalid User ID (must be a number)"
    except Exception as e:
        response = f"[ERROR] {e}"
    
    send_message(chat_id, response)


def make_admin_cmd(chat_id, user_id_str):
    """Make user admin"""
    try:
        user_id = int(user_id_str)
        admin_panel.add_admin(user_id)
        response = f"[OK] Admin enabled for {user_id}!"
    except ValueError:
        response = "[ERROR] Invalid User ID"
    except Exception as e:
        response = f"[ERROR] {e}"
    
    send_message(chat_id, response)


def remove_admin_cmd(chat_id, user_id_str):
    """Remove admin"""
    try:
        user_id = int(user_id_str)
        admin_panel.remove_admin(user_id)
        response = f"[OK] Admin removed for {user_id}!"
    except ValueError:
        response = "[ERROR] Invalid User ID"
    except Exception as e:
        response = f"[ERROR] {e}"
    
    send_message(chat_id, response)


def admin_list_cmd(chat_id):
    """Show admin list"""
    if not admin_panel.admins:
        response = "[INFO] No admins found"
    else:
        response = "[OK] Admin List:\n\n"
        for admin_id in sorted(admin_panel.admins):
            response += f"• {admin_id}\n"
    
    send_message(chat_id, response)


def users_list_cmd(chat_id):
    """Show all users"""
    import sqlite3
    
    try:
        conn = sqlite3.connect(subscription_manager.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT user_id, username, plan, status
            FROM users
            ORDER BY created_at DESC
            LIMIT 20
        ''')
        
        users = c.fetchall()
        conn.close()
        
        if not users:
            response = "[INFO] No users found"
        else:
            response = "[OK] Last 20 Users:\n\n"
            for user_id, username, plan, status in users:
                response += f"• {user_id} | {username} | {plan} | {status}\n"
    except Exception as e:
        response = f"[ERROR] {e}"
    
    send_message(chat_id, response)


def user_info_cmd(chat_id, user_id_str):
    """Get user info"""
    try:
        user_id = int(user_id_str)
        info = subscription_manager.check_subscription(user_id)
        
        if not info.get('exists'):
            response = f"[ERROR] User {user_id} not found"
        else:
            response = f"""[OK] User Info:

ID: {user_id}
Plan: {info.get('plan', 'N/A')}
Status: {info.get('status', 'N/A')}
Active: {'Yes' if info.get('is_active') else 'No'}
Days Left: {info.get('days_left', 0)}
Referral Code: {info.get('referral_code', 'N/A')}"""
    
    except ValueError:
        response = "[ERROR] Invalid User ID"
    except Exception as e:
        response = f"[ERROR] {e}"
    
    send_message(chat_id, response)


def upgrade_user_cmd(chat_id, user_id_str, plan):
    """Upgrade user subscription"""
    try:
        user_id = int(user_id_str)
        success, msg = subscription_manager.upgrade_user(
            user_id, 
            plan, 
            payment_method='admin_bot'
        )
        
        if success:
            response = f"[OK] Upgraded!\n\n{msg}"
        else:
            response = f"[ERROR] {msg}"
    
    except ValueError:
        response = "[ERROR] Invalid User ID"
    except Exception as e:
        response = f"[ERROR] {e}"
    
    send_message(chat_id, response)


def delete_user_cmd(chat_id, user_id_str):
    """Delete user"""
    try:
        user_id = int(user_id_str)
        import sqlite3
        
        conn = sqlite3.connect(subscription_manager.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        response = f"[OK] User {user_id} deleted!"
    except ValueError:
        response = "[ERROR] Invalid User ID"
    except Exception as e:
        response = f"[ERROR] {e}"
    
    send_message(chat_id, response)


def get_start_message():
    """Welcome message"""
    return """
<b>Welcome to Gold Analyzer VIP Bot!</b>

This is your trading signals platform.

<b>Available Plans:</b>
• Trial - 3 days free
• Bronze - $29/month
• Silver - $69/3 months
• Gold - $199/year
• Platinum - $499/year

Type /help for commands
"""


def handle_admin_command(chat_id, user_id, text):
    """Handle admin commands"""
    
    if text == '/add_user':
        response = """Send user data in format:
USER_ID USERNAME FIRST_NAME

Example:
123456789 ahmed_user Ahmed"""
        send_message(chat_id, response)
        ADMIN_COMMANDS[user_id] = 'add_user'
        
    elif text == '/make_admin':
        response = """Send User ID:
Example: 123456789"""
        send_message(chat_id, response)
        ADMIN_COMMANDS[user_id] = 'make_admin'
        
    elif text == '/remove_admin':
        response = """Send User ID to remove admin:
Example: 123456789"""
        send_message(chat_id, response)
        ADMIN_COMMANDS[user_id] = 'remove_admin'
        
    elif text == '/admin_list':
        admin_list_cmd(chat_id)
        
    elif text == '/users_list':
        users_list_cmd(chat_id)
        
    elif text == '/upgrade':
        response = """Send upgrade request in format:
USER_ID PLAN

Plans: bronze, silver, gold, platinum

Example:
123456789 gold"""
        send_message(chat_id, response)
        ADMIN_COMMANDS[user_id] = 'upgrade'
        
    elif text == '/user_info':
        response = """Send User ID:
Example: 123456789"""
        send_message(chat_id, response)
        ADMIN_COMMANDS[user_id] = 'user_info'
        
    elif text == '/delete_user':
        response = """Send User ID:
Example: 123456789"""
        send_message(chat_id, response)
        ADMIN_COMMANDS[user_id] = 'delete_user'


def handle_admin_input(chat_id, user_id, text):
    """Handle admin input data"""
    
    if user_id not in ADMIN_COMMANDS:
        return
    
    cmd = ADMIN_COMMANDS[user_id]
    parts = text.split()
    
    if cmd == 'add_user' and len(parts) >= 2:
        user_id_str = parts[0]
        username = parts[1]
        first_name = ' '.join(parts[2:]) if len(parts) > 2 else username
        add_user_admin(chat_id, user_id_str, username, first_name)
        del ADMIN_COMMANDS[user_id]
        
    elif cmd == 'make_admin' and len(parts) >= 1:
        make_admin_cmd(chat_id, parts[0])
        del ADMIN_COMMANDS[user_id]
        
    elif cmd == 'remove_admin' and len(parts) >= 1:
        remove_admin_cmd(chat_id, parts[0])
        del ADMIN_COMMANDS[user_id]
        
    elif cmd == 'upgrade' and len(parts) >= 2:
        upgrade_user_cmd(chat_id, parts[0], parts[1])
        del ADMIN_COMMANDS[user_id]
        
    elif cmd == 'user_info' and len(parts) >= 1:
        user_info_cmd(chat_id, parts[0])
        del ADMIN_COMMANDS[user_id]
        
    elif cmd == 'delete_user' and len(parts) >= 1:
        delete_user_cmd(chat_id, parts[0])
        del ADMIN_COMMANDS[user_id]


def handle_message(chat_id, user_id, text):
    """Process user message"""
    
    # Check admin commands first
    if is_admin(user_id) and text.startswith('/'):
        handle_admin_command(chat_id, user_id, text)
        return
    
    # Check admin input
    if user_id in ADMIN_COMMANDS:
        handle_admin_input(chat_id, user_id, text)
        return
    
    # Normal user commands
    if text == '/start':
        msg = get_start_message()
        send_message(chat_id, msg)
        
    elif text == '/subscribe':
        sub_info = subscription_manager.check_subscription(user_id)
        
        if sub_info.get('exists'):
            response = "Already subscribed!\n/status for details"
        else:
            success = subscription_manager.add_user(user_id, f"user_{user_id}")
            if success:
                response = "Success! Account created.\nYou are now subscribed.\n\nWait for signals..."
            else:
                response = "Error subscribing"
        
        send_message(chat_id, response)
        
    elif text == '/status':
        sub_info = subscription_manager.check_subscription(user_id)
        
        if not sub_info.get('exists'):
            response = "Not subscribed\n/subscribe to start"
        else:
            plan = sub_info.get('plan', 'unknown')
            days_left = sub_info.get('days_left', 0)
            response = f"Plan: {plan.upper()}\nDays left: {days_left}"
        
        send_message(chat_id, response)
        
    elif text == '/help':
        msg = get_help_message(user_id)
        send_message(chat_id, msg)
    
    elif text == '/plans':
        msg = """
<b>Available Plans:</b>

Trial: Free (3 days)
• 1 signal per day

Bronze: $29/month
• 3 signals per day
• 30 days

Silver: $69 for 3 months
• 5 signals per day
• 90 days

Gold: $199/year
• 7 signals per day
• 365 days

Platinum: $499/year
• 10 signals per day
• 365 days

Contact us for purchase
"""
        send_message(chat_id, msg)


def process_update(update):
    """Process Telegram update"""
    try:
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            text = message.get('text', '')
            
            if text:
                log_msg(f"Message from {user_id}: {text}")
                handle_message(chat_id, user_id, text)
                
    except Exception as e:
        log_msg(f"[ERROR] Process: {e}")


def get_updates():
    """Get updates from Telegram"""
    url = f"{BASE_URL}/getUpdates"
    last_update = load_last_update()
    
    payload = {"offset": last_update + 1}
    
    try:
        response = requests.get(url, json=payload, timeout=10)
        updates = response.json().get('result', [])
        
        for update in updates:
            process_update(update)
            update_id = update.get('update_id')
            if update_id:
                save_last_update(update_id)
        
        return len(updates)
    except Exception as e:
        log_msg(f"[ERROR] Get updates: {e}")
        return 0


def run_bot():
    """Main bot loop"""
    log_msg("Bot started!")
    log_msg(f"Token: {BOT_TOKEN[:20]}...")
    
    while True:
        try:
            count = get_updates()
            if count > 0:
                log_msg(f"Processed {count} messages")
            time.sleep(1)
        except KeyboardInterrupt:
            log_msg("Bot stopped!")
            break
        except Exception as e:
            log_msg(f"[ERROR] {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_bot()
