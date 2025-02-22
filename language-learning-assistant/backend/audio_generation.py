import boto3
import hashlib
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class AudioGenerator:
    def __init__(self, max_cache_size_mb: int = 100):
        """Initialize audio generator with caching"""
        self.polly = boto3.client('polly')
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'audio_cache')
        self.metadata_file = os.path.join(self.cache_dir, 'metadata.json')
        self.max_cache_size_mb = max_cache_size_mb
        self.voice_capabilities = {}
        self.error_log = []
        self.metadata = self._load_metadata()
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)

    def _load_metadata(self) -> Dict:
        """Load or create cache metadata"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                    # Handle timestamp conversion
                    if isinstance(metadata.get('last_cleanup'), str):
                        try:
                            dt = datetime.fromisoformat(metadata['last_cleanup'].replace('Z', '+00:00'))
                            metadata['last_cleanup'] = dt.timestamp()
                        except:
                            metadata['last_cleanup'] = time.time()
                    return metadata
            except json.JSONDecodeError:
                pass
        
        # Initialize new metadata
        return {
            'files': {},
            'total_size_bytes': 0,
            'last_cleanup': time.time(),
            'max_size_mb': self.max_cache_size_mb
        }

    def _save_metadata(self):
        """Save cache metadata"""
        with open(self.metadata_file, 'w') as f:
            # Convert timestamp to ISO format for better readability
            metadata_to_save = self.metadata.copy()
            metadata_to_save['last_cleanup'] = datetime.fromtimestamp(
                self.metadata['last_cleanup']
            ).isoformat()
            json.dump(metadata_to_save, f, indent=2, ensure_ascii=False)

    def _get_cache_key(self, text: str, voice_id: str) -> str:
        """Generate cache key from text and voice"""
        content = f"{text}_{voice_id}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

    def _cleanup_cache(self):
        """Remove least recently used files if cache exceeds size limit"""
        if self.metadata['total_size_bytes'] <= self.max_cache_size_mb * 1024 * 1024:
            return

        # Sort files by last access time
        files = sorted(
            self.metadata['files'].items(),
            key=lambda x: x[1]['last_accessed']
        )

        # Remove files until we're under the limit
        for file_hash, info in files:
            file_path = os.path.join(self.cache_dir, f"{file_hash}.mp3")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            self.metadata['total_size_bytes'] -= info['size_bytes']
            del self.metadata['files'][file_hash]
            
            if self.metadata['total_size_bytes'] <= self.max_cache_size_mb * 1024 * 1024:
                break

        self._save_metadata()

    def _log_error(self, error_type: str, detail: str, voice_id: Optional[str] = None):
        """Log an error with timestamp"""
        self.error_log.append({
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'detail': detail,
            'voice_id': voice_id
        })
        if len(self.error_log) > 100:  # Keep last 100 errors
            self.error_log = self.error_log[-100:]

    def check_voice_capability(self, voice_id: str) -> Dict:
        """Check if voice supports neural engine, cache result"""
        if voice_id not in self.voice_capabilities:
            try:
                response = self.polly.describe_voice(VoiceId=voice_id)
                self.voice_capabilities[voice_id] = {
                    'supports_neural': 'neural' in response['SupportedEngines'],
                    'engines': response['SupportedEngines']
                }
            except Exception as e:
                print(f"[AUDIO] Error checking voice capability: {str(e)}")
                self.voice_capabilities[voice_id] = {
                    'supports_neural': False,
                    'engines': ['standard']
                }
        
        return self.voice_capabilities[voice_id]

    def get_available_voices(self) -> List[Dict]:
        """Get list of available Japanese voices"""
        try:
            response = self.polly.describe_voices(LanguageCode='ja-JP')
            return response['Voices']
        except Exception as e:
            print(f"[AUDIO] Error getting voices: {str(e)}")
            return []

    def generate_audio(self, text: str, voice_id: str = "Mizuki") -> Optional[str]:
        """Generate audio with caching and voice capability checking"""
        try:
            # Generate cache key and check cache
            cache_key = self._get_cache_key(text, voice_id)
            cache_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")

            # Check if valid cached file exists
            if cache_key in self.metadata['files'] and os.path.exists(cache_path):
                # Update last accessed time
                self.metadata['files'][cache_key]['last_accessed'] = time.time()
                self._save_metadata()
                return cache_path

            # Check voice capabilities
            voice_info = self.check_voice_capability(voice_id)
            engine = 'neural' if voice_info['supports_neural'] else 'standard'

            # Generate audio with fallback
            try:
                response = self.polly.synthesize_speech(
                    Text=text,
                    OutputFormat='mp3',
                    VoiceId=voice_id,
                    Engine=engine
                )
            except Exception as e:
                if 'ValidationException' in str(e) and engine == 'neural':
                    # Log the neural engine failure
                    self._log_error('neural_engine_failed', str(e), voice_id)
                    # Fallback to standard engine
                    response = self.polly.synthesize_speech(
                        Text=text,
                        OutputFormat='mp3',
                        VoiceId=voice_id,
                        Engine='standard'
                    )
                    # Update voice capabilities cache
                    self.voice_capabilities[voice_id]['supports_neural'] = False
                else:
                    raise

            # Save to cache
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(cache_path, 'wb') as f:
                f.write(response['AudioStream'].read())

            # Update metadata
            file_size = os.path.getsize(cache_path)
            self.metadata['files'][cache_key] = {
                'size_bytes': file_size,
                'last_accessed': time.time(),
                'text': text,
                'voice_id': voice_id,
                'engine': engine
            }
            self.metadata['total_size_bytes'] = sum(
                f['size_bytes'] for f in self.metadata['files'].values()
            )
            self._save_metadata()

            # Run cleanup if needed
            self._cleanup_cache()

            return cache_path

        except Exception as e:
            self._log_error('generation_failed', str(e), voice_id)
            return None

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size_mb': self.metadata['total_size_bytes'] / (1024 * 1024),
            'max_size_mb': self.max_cache_size_mb,
            'file_count': len(self.metadata['files']),
            'last_cleanup': datetime.fromtimestamp(
                self.metadata['last_cleanup']
            ).strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_error_stats(self) -> Dict:
        """Get statistics about errors"""
        stats = {
            'total_errors': len(self.error_log),
            'neural_failures': 0,
            'generation_failures': 0,
            'voice_stats': {}
        }
        
        for error in self.error_log:
            if error['type'] == 'neural_engine_failed':
                stats['neural_failures'] += 1
            elif error['type'] == 'generation_failed':
                stats['generation_failures'] += 1
                
            if error['voice_id']:
                voice_stats = stats['voice_stats'].setdefault(error['voice_id'], {
                    'neural_failures': 0,
                    'generation_failures': 0
                })
                if error['type'] == 'neural_engine_failed':
                    voice_stats['neural_failures'] += 1
                elif error['type'] == 'generation_failed':
                    voice_stats['generation_failures'] += 1
        
        return stats

    def clear_cache(self):
        """Clear all cached files"""
        try:
            for file_hash in self.metadata['files'].keys():
                file_path = os.path.join(self.cache_dir, f"{file_hash}.mp3")
                if os.path.exists(file_path):
                    os.remove(file_path)

            self.metadata = {'files': {}, 'total_size_bytes': 0, 'last_cleanup': time.time()}
            self._save_metadata()
            return True
        except Exception as e:
            print(f"[AUDIO] Error clearing cache: {str(e)}")
            return False