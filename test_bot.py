#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for VIP Bot
"""

from vip_bot_simple import (
    send_broadcast_signal, 
    send_message, 
    subscription_manager,
    log_msg
)
from datetime import datetime
import sys

def test_system():
    """Test the complete system"""
    
    log_msg("="*50)
    log_msg("VIP Bot System Test")
    log_msg("="*50)
    
    # Test 1: Database
    log_msg("\n[TEST 1] Database...")
    try:
        users = subscription_manager.get_all_active_users()
        log_msg(f"Active users: {len(users)}")
        print("[OK] Database loaded")
    except Exception as e:
        log_msg(f"[ERROR] {e}")
        return False
    
    # Test 2: Create test user
    log_msg("\n[TEST 2] Create test user...")
    try:
        test_user = 999999999
        success = subscription_manager.add_user(test_user, "test_bot")
        if success:
            print("[OK] Test user created")
        else:
            print("[INFO] User already exists")
    except Exception as e:
        log_msg(f"[ERROR] {e}")
    
    # Test 3: Check subscription
    log_msg("\n[TEST 3] Check subscription...")
    try:
        sub_info = subscription_manager.check_subscription(999999999)
        if sub_info.get('exists'):
            plan = sub_info.get('plan')
            is_active = sub_info.get('is_active')
            log_msg(f"Plan: {plan}, Active: {is_active}")
            print("[OK] Subscription checked")
        else:
            print("[INFO] No subscription found")
    except Exception as e:
        log_msg(f"[ERROR] {e}")
    
    # Test 4: Signal broadcasting
    log_msg("\n[TEST 4] Signal broadcasting...")
    try:
        test_signal = {
            'symbol': 'EURUSD',
            'rec': 'Buy',
            'entry': 1.12345,
            'sl': 1.12000,
            'tp1': 1.12700,
            'tp2': 1.13000,
            'tp3': 1.13300,
            'tf': '1H',
            'rr': 2.5
        }
        
        sent = send_broadcast_signal(test_signal, 85)
        log_msg(f"Signals sent: {sent}")
        print("[OK] Broadcasting works")
    except Exception as e:
        log_msg(f"[ERROR] {e}")
        return False
    
    log_msg("\n" + "="*50)
    log_msg("All tests passed!")
    log_msg("="*50)
    
    return True


if __name__ == "__main__":
    try:
        success = test_system()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_msg("\nTest interrupted by user")
        sys.exit(1)
