"""Test audio generation functionality"""
import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from backend.audio_generation import AudioGenerator
from backend.audio_cache import AudioCache

def test_audio_generation():
    try:
        # Initialize components
        ag = AudioGenerator()
        cache = AudioCache(os.path.join(os.path.dirname(__file__), 'audio_cache'))
        
        # Test cache validation and cleanup
        print("\nValidating cache...")
        cache.validate_cache()
        
        if "--cleanup" in sys.argv:
            print("\nCleaning old files...")
            cleanup_stats = cache.clean_old_files()
            print(f"Removed {cleanup_stats['files_removed']} files")
            print(f"Freed {cleanup_stats['bytes_freed'] / 1024 / 1024:.2f}MB")
            print(f"Remaining: {cleanup_stats['remaining_files']} files, {cleanup_stats['remaining_size_mb']:.2f}MB")
            return

        # Show cache stats
        print("\nCache statistics:")
        stats = ag.get_cache_stats()
        print(f"Cache size: {stats['cache_size_mb']:.2f}MB / {stats['max_size_mb']}MB")
        print(f"File count: {stats['file_count']}")
        print(f"Last cleanup: {stats['last_cleanup']}")
        
        # Test voice capabilities
        print("\nChecking voice capabilities...")
        voices = ["Tomoko", "Mizuki", "Takumi", "Kazuha"]
        for voice in voices:
            try:
                caps = ag.check_voice_capability(voice)
                print(f"{voice}: {caps}")
            except (ClientError, NoCredentialsError) as e:
                print(f"Could not check {voice} capabilities: {str(e)}")
                break
        
        # Test audio generation if we have credentials
        test_text = "こんにちは、お元気ですか？"
        try:
            print(f"\nTesting audio generation with Mizuki (standard)...")
            result = ag.generate_audio(test_text, "Mizuki")
            if result:
                print(f"Generated file: {os.path.basename(result)}")
            else:
                print("Generation failed")
        except (ClientError, NoCredentialsError) as e:
            print(f"Audio generation failed: {str(e)}")
            print("Please ensure AWS credentials are configured correctly")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_audio_generation()