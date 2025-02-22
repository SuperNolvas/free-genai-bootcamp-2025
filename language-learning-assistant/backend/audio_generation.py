import boto3
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .audio_cache import AudioCache  # Add missing import

class AudioGenerator:
    def __init__(self):
        """Initialize audio generator with caching"""
        self.polly = boto3.client('polly')
        self.cache = AudioCache(
            os.path.join(os.path.dirname(__file__), 'audio_cache'),
            max_age_days=30,
            max_size_mb=100
        )
        self.voice_capabilities = {}
        self.error_log = []

    def _get_cache_key(self, text: str, voice_id: str) -> str:
        """Generate cache key from text and voice"""
        content = f"{text}_{voice_id}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

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
            cached_path = self.cache.get_file_path(cache_key)

            if cached_path:
                self.cache.touch_file(cache_key)
                return cached_path

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
                    engine = 'standard'
                    response = self.polly.synthesize_speech(
                        Text=text,
                        OutputFormat='mp3',
                        VoiceId=voice_id,
                        Engine=engine
                    )
                    # Update voice capabilities cache
                    self.voice_capabilities[voice_id]['supports_neural'] = False
                else:
                    raise

            # Read audio data
            audio_data = response['AudioStream'].read()

            # Add to cache with metadata
            return self.cache.add_file(cache_key, audio_data, {
                'text': text,
                'voice_id': voice_id,
                'engine': engine
            })

        except Exception as e:
            self._log_error('generation_failed', str(e), voice_id)
            return None

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return self.cache.get_stats()

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
        # This now delegates to AudioCache's cleanup methods
        self.cache.clean_old_files()
        return True