"""
MODUŁ POWIADOMIEŃ - Notification System
Obsługuje: staff messages, announcements, password resets
"""

import datetime
import json
import os

DATA_FILE = "dane_aplikacji.json"

def load_notifications_data(data_store):
    """Załaduj dane powiadomień z globalnego stanu"""
    if "notifications" not in data_store:
        data_store["notifications"] = {
            "unread_staff_messages": 0,
            "unread_announcements": 0,
            "unread_password_resets": 0,
            "notification_history": [],
            "user_notifications": {}
        }
    return data_store["notifications"]

def add_notification(data_store, user_key, notif_type, title, message, sender_nick="System"):
    """
    Dodaj nowe powiadomienie dla użytkownika
    
    notif_type: "staff_message", "announcement", "password_reset"
    """
    notif_data = load_notifications_data(data_store)
    
    if user_key not in notif_data["user_notifications"]:
        notif_data["user_notifications"][user_key] = {
            "unread": [],
            "read": []
        }
    
    notification = {
        "id": len(notif_data["notification_history"]),
        "type": notif_type,
        "title": title,
        "message": message,
        "sender": sender_nick,
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "read": False,
        "for_user": user_key
    }
    
    notif_data["user_notifications"][user_key]["unread"].append(notification)
    notif_data["notification_history"].append(notification)
    
    # Aktualizuj liczniki
    if notif_type == "staff_message":
        notif_data["unread_staff_messages"] += 1
    elif notif_type == "announcement":
        notif_data["unread_announcements"] += 1
    elif notif_type == "password_reset":
        notif_data["unread_password_resets"] += 1
    
    return notification

def get_user_notifications(data_store, user_key):
    """Pobierz wszystkie powiadomienia użytkownika"""
    notif_data = load_notifications_data(data_store)
    
    if user_key not in notif_data["user_notifications"]:
        notif_data["user_notifications"][user_key] = {"unread": [], "read": []}
    
    return notif_data["user_notifications"][user_key]

def mark_as_read(data_store, user_key, notif_id):
    """Oznacz powiadomienie jako przeczytane"""
    notif_data = load_notifications_data(data_store)
    
    if user_key in notif_data["user_notifications"]:
        user_notifs = notif_data["user_notifications"][user_key]
        
        for notif in user_notifs["unread"]:
            if notif.get("id") == notif_id:
                notif["read"] = True
                user_notifs["read"].append(notif)
                user_notifs["unread"].remove(notif)
                break

def get_unread_count(data_store, user_key):
    """Pobierz liczbę nieprzeczytanych powiadomień"""
    user_notifs = get_user_notifications(data_store, user_key)
    return len(user_notifs.get("unread", []))

def get_notification_summary(data_store, user_key):
    """Pobierz podsumowanie powiadomień dla użytkownika"""
    user_notifs = get_user_notifications(data_store, user_key)
    unread = user_notifs.get("unread", [])
    
    summary = {
        "total_unread": len(unread),
        "staff_messages": len([n for n in unread if n.get("type") == "staff_message"]),
        "announcements": len([n for n in unread if n.get("type") == "announcement"]),
        "password_resets": len([n for n in unread if n.get("type") == "password_reset"]),
        "recent": unread[:5] if unread else []
    }
    
    return summary

def clear_old_notifications(data_store, days=30):
    """Wyczyść stare powiadomienia (starsze niż N dni)"""
    import time
    notif_data = load_notifications_data(data_store)
    
    cutoff_time = time.time() - (days * 86400)
    
    for user_key in notif_data["user_notifications"]:
        user_notifs = notif_data["user_notifications"][user_key]
        
        # Czyszczenie przeczytanych
        user_notifs["read"] = [
            n for n in user_notifs["read"]
            if datetime.datetime.strptime(n["timestamp"], '%Y-%m-%d %H:%M:%S').timestamp() > cutoff_time
        ]
