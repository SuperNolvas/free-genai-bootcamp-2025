"""Audio cache module for storing generated audio files"""

import os
import json
import shutil
import time
from typing import Optional, Dict
from datetime import datetime, timedelta

class AudioCache:
    def __init__(self, cache_dir: Optional[str] = None, max_age_days: int = 30, max_size_mb: int = 100):
        if cache_dir is None:
            cache_dir = os.path.dirname(__file__)
        self.cache_dir = cache_dir
        self.metadata_path = os.path.join(cache_dir, 'metadata.json')
        self.max_age_days = max_age_days
        self.max_size_mb = max_size_mb
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict:
        """Load or create cache metadata"""
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
        return {
            'files': {},
            'total_size_bytes': 0,
            'last_cleanup': time.time(),
            'max_size_mb': self.max_size_mb
        }
    
    def _save_metadata(self):
        """Save cache metadata"""
        with open(self.metadata_path, 'w') as f:
            # Convert timestamp to ISO format for better readability
            metadata_to_save = self.metadata.copy()
            metadata_to_save['last_cleanup'] = datetime.fromtimestamp(
                self.metadata['last_cleanup']
            ).isoformat()
            json.dump(metadata_to_save, f, indent=2, ensure_ascii=False)

    def get_file_path(self, file_hash: str) -> Optional[str]:
        """Get path if file exists in cache"""
        path = os.path.join(self.cache_dir, f"{file_hash}.mp3")
        return path if os.path.exists(path) else None

    def add_file(self, file_hash: str, file_data: bytes, metadata: Dict) -> str:
        """Add a file to the cache with metadata"""
        file_path = os.path.join(self.cache_dir, f"{file_hash}.mp3")
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)
            
        # Update metadata
        file_size = os.path.getsize(file_path)
        self.metadata['files'][file_hash] = {
            'size_bytes': file_size,
            'last_accessed': time.time(),
            **metadata
        }
        self.metadata['total_size_bytes'] = sum(
            f['size_bytes'] for f in self.metadata['files'].values()
        )
        self._save_metadata()
        
        # Run cleanup if needed
        self._cleanup_by_size()
        return file_path

    def touch_file(self, file_hash: str):
        """Update last access time of a file"""
        if file_hash in self.metadata['files']:
            self.metadata['files'][file_hash]['last_accessed'] = time.time()
            self._save_metadata()

    def _cleanup_by_size(self):
        """Remove least recently used files if cache exceeds size limit"""
        if self.metadata['total_size_bytes'] <= self.max_size_mb * 1024 * 1024:
            return

        # Sort files by last access time
        files = sorted(
            [(h, i) for h, i in self.metadata['files'].items()
             if os.path.exists(self.get_file_path(h))],
            key=lambda x: x[1]['last_accessed']
        )

        bytes_to_free = self.metadata['total_size_bytes'] - (self.max_size_mb * 1024 * 1024)
        bytes_freed = 0
        files_removed = []

        for file_hash, info in files:
            if bytes_freed >= bytes_to_free:
                break

            file_path = self.get_file_path(file_hash)
            if file_path:
                try:
                    os.remove(file_path)
                    bytes_freed += info['size_bytes']
                    files_removed.append(file_hash)
                except OSError:
                    continue

        # Update metadata
        for file_hash in files_removed:
            del self.metadata['files'][file_hash]

        self.metadata['total_size_bytes'] -= bytes_freed
        self.metadata['last_cleanup'] = time.time()
        self._save_metadata()

    def clean_old_files(self) -> Dict:
        """Remove files that haven't been accessed in max_age_days"""
        current_time = time.time()
        cutoff_time = current_time - (self.max_age_days * 24 * 60 * 60)
        
        files_removed = 0
        bytes_freed = 0
        
        # Identify old files
        for file_hash, file_info in list(self.metadata['files'].items()):
            last_accessed = file_info['last_accessed']
            if last_accessed < cutoff_time:
                file_path = self.get_file_path(file_hash)
                if file_path:
                    bytes_freed += file_info['size_bytes']
                    os.remove(file_path)
                    files_removed += 1
                    del self.metadata['files'][file_hash]
        
        # Update metadata
        self.metadata['total_size_bytes'] = max(0, self.metadata['total_size_bytes'] - bytes_freed)
        self.metadata['last_cleanup'] = current_time
        self._save_metadata()
        
        return {
            'files_removed': files_removed,
            'bytes_freed': bytes_freed,
            'remaining_files': len(self.metadata['files']),
            'remaining_size_mb': self.metadata['total_size_bytes'] / (1024 * 1024)
        }
        
    def validate_cache(self):
        """Validate cache and fix any inconsistencies"""
        actual_files = {f.replace('.mp3', '') for f in os.listdir(self.cache_dir) 
                       if f.endswith('.mp3')}
        metadata_files = set(self.metadata['files'].keys())
        
        # Remove missing files from metadata
        for file_hash in metadata_files - actual_files:
            if file_hash in self.metadata['files']:
                del self.metadata['files'][file_hash]
        
        # Update total size
        self.metadata['total_size_bytes'] = sum(
            os.path.getsize(self.get_file_path(h))
            for h in self.metadata['files']
            if self.get_file_path(h)
        )
        self._save_metadata()

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size_mb': self.metadata['total_size_bytes'] / (1024 * 1024),
            'max_size_mb': self.max_size_mb,
            'file_count': len(self.metadata['files']),
            'last_cleanup': datetime.fromtimestamp(
                self.metadata['last_cleanup']
            ).strftime('%Y-%m-%d %H:%M:%S')
        }