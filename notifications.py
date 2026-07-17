"""System powiadomień dla aplikacji Koder"""

class NotificationManager:
    """Zarządza powiadomieniami dla użytkowników"""
    
    @staticmethod
    def add_notification(data, user_id, notification_type, message, icon="ℹ️"):
        """Dodaje nowe powiadomienie"""
        if "notifications" not in data:
            data["notifications"] = {}
        if user_id not in data["notifications"]:
            data["notifications"][user_id] = []
        
        notification = {
            "type": notification_type,
            "message": message,
            "icon": icon,
            "read": False
        }
        data["notifications"][user_id].append(notification)
        return notification
    
    @staticmethod
    def get_unread_count(data, user_id):
        """Zwraca liczbę nieprzeczytanych powiadomień"""
        if "notifications" not in data or user_id not in data["notifications"]:
            return 0
        return sum(1 for n in data["notifications"][user_id] if not n.get("read", False))
    
    @staticmethod
    def get_notifications(data, user_id):
        """Zwraca wszystkie powiadomienia użytkownika"""
        if "notifications" not in data or user_id not in data["notifications"]:
            return []
        return data["notifications"][user_id]
    
    @staticmethod
    def mark_as_read(data, user_id, index):
        """Oznacza powiadomienie jako przeczytane"""
        if "notifications" in data and user_id in data["notifications"]:
            if 0 <= index < len(data["notifications"][user_id]):
                data["notifications"][user_id][index]["read"] = True
                return True
        return False
    
    @staticmethod
    def clear_notifications(data, user_id):
        """Czyści wszystkie powiadomienia użytkownika"""
        if "notifications" in data and user_id in data["notifications"]:
            data["notifications"][user_id] = []
            return True
        return False


# Typy powiadomień
NOTIFICATION_TYPES = {
    "message": "💬",
    "password_reset": "🔑",
    "announcement": "📢",
    "role_change": "👑",
    "system": "⚙️",
    "warning": "⚠️",
    "success": "✅",
    "error": "❌",
    "info": "ℹ️"
}
