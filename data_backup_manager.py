import json
import time
import os
from typing import Dict
from redis_card_manager import RedisCardManager

class DataBackupManager:
    def __init__(self, redis_manager: RedisCardManager):
        self.redis = redis_manager
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup_to_json(self, backup_path: str = None):
        """Backup Redis data to JSON file"""
        if not self.redis.redis_available:
            print("Redis not available, cannot backup")
            return False

        if backup_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f'cards_backup_{timestamp}.json')

        try:
            backup_data = {}
            # Get all card keys
            card_keys = self.redis.redis_client.keys("card:*")

            for key in card_keys:
                if not key.endswith((':counters', ':synergies', ':countered_by')):
                    card_name = key.replace("card:", "")
                    card_data = self.redis.redis_client.hgetall(key)

                    # Get counters, synergies, etc.
                    counters_key = f"{key}:counters"
                    synergies_key = f"{key}:synergies"
                    countered_by_key = f"{key}:countered_by"

                    if self.redis.redis_client.exists(counters_key):
                        card_data['counters'] = self.redis.redis_client.zrange(counters_key, 0, -1)
                    if self.redis.redis_client.exists(synergies_key):
                        card_data['synergies'] = self.redis.redis_client.zrange(synergies_key, 0, -1)
                    if self.redis.redis_client.exists(countered_by_key):
                        card_data['countered_by'] = self.redis.redis_client.zrange(countered_by_key, 0, -1)

                    backup_data[card_name] = card_data

            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)

            print(f"Backup completed: {backup_path}")
            return True

        except Exception as e:
            print(f"Backup failed: {e}")
            return False

    def restore_from_json(self, backup_path: str):
        """Restore Redis data from JSON backup"""
        if not self.redis.redis_available:
            print("Redis not available, cannot restore")
            return False

        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            restored_count = 0
            for card_name, card_data in backup_data.items():
                if self.redis.store_card(card_name, card_data):
                    restored_count += 1

            print(f"Restored {restored_count} cards from {backup_path}")
            return True

        except Exception as e:
            print(f"Restore failed: {e}")
            return False

    def auto_backup(self, interval_seconds: int = 1800):
        """Perform automatic backup if enough time has passed"""
        backup_marker_file = os.path.join(self.backup_dir, "last_backup.txt")
        
        try:
            if os.path.exists(backup_marker_file):
                with open(backup_marker_file, 'r') as f:
                    last_backup_time = float(f.read().strip())
            else:
                last_backup_time = 0

            current_time = time.time()
            if current_time - last_backup_time >= interval_seconds:
                if self.backup_to_json():
                    with open(backup_marker_file, 'w') as f:
                        f.write(str(current_time))
                    return True

        except Exception as e:
            print(f"Auto backup failed: {e}")

        return False

    def cleanup_old_backups(self, keep_count: int = 10):
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('cards_backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    backup_files.append((filepath, os.path.getmtime(filepath)))

            # Sort by modification time, newest first
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups
            removed_count = 0
            for filepath, _ in backup_files[keep_count:]:
                try:
                    os.remove(filepath)
                    removed_count += 1
                except Exception as e:
                    print(f"Failed to remove old backup {filepath}: {e}")

            if removed_count > 0:
                print(f"Cleaned up {removed_count} old backup files")

        except Exception as e:
            print(f"Backup cleanup failed: {e}")

    def get_backup_info(self) -> Dict:
        """Get information about available backups"""
        info = {
            'backup_count': 0,
            'latest_backup': None,
            'oldest_backup': None,
            'total_size_mb': 0
        }

        try:
            backup_files = []
            total_size = 0

            for filename in os.listdir(self.backup_dir):
                if filename.startswith('cards_backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    size = os.path.getsize(filepath)
                    backup_files.append((filepath, mtime))
                    total_size += size

            info['backup_count'] = len(backup_files)
            info['total_size_mb'] = total_size / (1024 * 1024)

            if backup_files:
                backup_files.sort(key=lambda x: x[1])
                info['oldest_backup'] = os.path.basename(backup_files[0][0])
                info['latest_backup'] = os.path.basename(backup_files[-1][0])

        except Exception as e:
            print(f"Failed to get backup info: {e}")

        return info
