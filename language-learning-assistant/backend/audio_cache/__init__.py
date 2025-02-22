"""Audio cache module for storing generated audio files"""

import os
import json
import shutil
import time
from typing import Optional, Dict
from datetime import datetime, timedelta

class AudioCache:
    def __init__(self, cache_dir: Optional[str] = None, max_age_days: int = 30):
        if cache_dir is None:
            cache_dir = os.path.dirname(__file__)
        self.cache_dir = cache_dir
        self.metadata_path = os.path.join(cache_dir, 'metadata.json')
        self.max_age_days = max_age_days
        
    def get_file_path(self, file_hash: str) -> str:
        """Get full path for a cached file"""
        return os.path.join(self.cache_dir, f"{file_hash}.mp3")
    
    def get_metadata(self) -> Dict:
        """Get cache metadata"""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                    # Convert string timestamp to float if needed
                    if isinstance(metadata.get('last_cleanup'), str):
                        try:
                            dt = datetime.fromisoformat(metadata['last_cleanup'].replace('Z', '+00:00'))
                            metadata['last_cleanup'] = dt.timestamp()
                        except:
                            metadata['last_cleanup'] = time.time()
                    return metadata
            except json.JSONDecodeError:
                pass
        return {'files': {}, 'total_size_bytes': 0, 'last_cleanup': time.time()}

    def clean_old_files(self) -> Dict:
        """Remove files that haven't been accessed in max_age_days"""
        metadata = self.get_metadata()
        current_time = time.time()
        cutoff_time = current_time - (self.max_age_days * 24 * 60 * 60)
        
        files_removed = 0
        bytes_freed = 0
        
        # Identify old files
        for file_hash, file_info in list(metadata['files'].items()):
            last_accessed = datetime.fromisoformat(file_info['last_accessed']).timestamp()
            if last_accessed < cutoff_time:
                file_path = self.get_file_path(file_hash)
                if os.path.exists(file_path):
                    bytes_freed += file_info['size_bytes']
                    os.remove(file_path)
                    files_removed += 1
                del metadata['files'][file_hash]
        
        # Update metadata
        metadata['total_size_bytes'] = max(0, metadata['total_size_bytes'] - bytes_freed)
        metadata['last_cleanup'] = current_time
        
        with open(self.metadata_path, 'w') as f:
            metadata_to_save = metadata.copy()
            metadata_to_save['last_cleanup'] = datetime.fromtimestamp(current_time).isoformat()
            json.dump(metadata_to_save, f, indent=2, ensure_ascii=False)
            
        return {
            'files_removed': files_removed,
            'bytes_freed': bytes_freed,
            'remaining_files': len(metadata['files']),
            'remaining_size_mb': metadata['total_size_bytes'] / (1024 * 1024)
        }
        
    def calculate_total_size(self) -> int:
        """Calculate actual total size of cached files"""
        total = 0
        for file in os.listdir(self.cache_dir):
            if file.endswith('.mp3'):
                path = os.path.join(self.cache_dir, file)
                total += os.path.getsize(path)
        return total
    
    def validate_cache(self):
        """Validate cache and fix any inconsistencies"""
        metadata = self.get_metadata()
        actual_files = {f.replace('.mp3', '') for f in os.listdir(self.cache_dir) 
                       if f.endswith('.mp3')}
        metadata_files = set(metadata['files'].keys())
        
        # Remove missing files from metadata
        for file_hash in metadata_files - actual_files:
            if file_hash in metadata['files']:
                del metadata['files'][file_hash]
        
        # Update total size
        metadata['total_size_bytes'] = self.calculate_total_size()
        
        # Save corrected metadata
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _cleanup_cache(self):
        """Remove least recently used files if cache exceeds size limit"""
        if self.metadata['total_size_bytes'] <= self.max_cache_size_mb * 1024 * 1024:
            return

        # Sort files by last access time
        files = sorted(
            [
                (hash_, info) for hash_, info in self.metadata['files'].items()
                if os.path.exists(self.get_file_path(hash_))  # Only consider existing files
            ],
            key=lambda x: x[1]['last_accessed']
        )

        bytes_to_free = self.metadata['total_size_bytes'] - (self.max_cache_size_mb * 1024 * 1024)
        bytes_freed = 0
        files_removed = []

        # Remove files until we're under the limit
        for file_hash, info in files:
            if bytes_freed >= bytes_to_free:
                break

            file_path = self.get_file_path(file_hash)
            try:
                os.remove(file_path)
                bytes_freed += info['size_bytes']
                files_removed.append(file_hash)
            except OSError as e:
                self._log_error('cleanup_failed', f"Failed to remove {file_hash}: {str(e)}")
                continue

        # Update metadata
        for file_hash in files_removed:
            del self.metadata['files'][file_hash]

        self.metadata['total_size_bytes'] -= bytes_freed
        self.metadata['last_cleanup'] = time.time()
        self._save_metadata()

        # Log cleanup results
        self._log_error('cleanup_completed', 
                       f"Freed {bytes_freed/(1024*1024):.2f}MB by removing {len(files_removed)} files")

    def _get_file_path(self, file_hash: str) -> str:
        """Get full path for a cached file"""
        return os.path.join(self.cache_dir, f"{file_hash}.mp3")

    def get_file_path(self, file_hash: str) -> Optional[str]:
        """Get path if file exists in cache"""
        path = self._get_file_path(file_hash)
        return path if os.path.exists(path) else None