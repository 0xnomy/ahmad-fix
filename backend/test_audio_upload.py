#!/usr/bin/env python3
"""
Audio Upload and Video Generation Test Script
Tests the audio upload functionality and creates videos using Remotion
"""

import asyncio
import requests
import os
import time
import shutil
from pathlib import Path
import json
from typing import Dict, Any, List
import sys
from app.remotion_service import RemotionService
from app.models import GeneratedImage

# Configuration
BASE_URL = "http://localhost:8000"
TEST_AUDIO_DIR = Path(__file__).parent / "test_audio"
GENERATED_DIR = Path(__file__).parent.parent / "generated"
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"

# Specific test file and images
TEST_AUDIO_FILE = Path(r"C:\Users\nauma\Downloads\test.mp3")
EXPECTED_IMAGES = 2  # Use 2 images from generated folder

class AudioVideoTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.remotion_service = RemotionService()

    def log_test_result(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """Log a test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
        print()

    def get_user_audio_file(self) -> Path:
        """Get the hardcoded audio file"""
        print("\n🎵 Audio File Selection")
        print("-" * 30)

        audio_file_path = TEST_AUDIO_FILE

        if not audio_file_path.exists():
            raise FileNotFoundError(f"Test audio file not found: {audio_file_path}")

        if not audio_file_path.is_file():
            raise ValueError(f"Path is not a file: {audio_file_path}")

        # Check file extension
        valid_extensions = ['.mp3', '.wav', '.m4a', '.aac']
        if audio_file_path.suffix.lower() not in valid_extensions:
            raise ValueError(f"Invalid file type. Supported formats: {', '.join(valid_extensions)}")

        # Check file size (max 10MB)
        file_size_mb = audio_file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 10:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB (max 10MB)")

        print(f"✅ Using test audio file: {audio_file_path.name} ({file_size_mb:.1f}MB)")
        return audio_file_path

    def copy_audio_to_generated(self, audio_file_path: Path) -> Path:
        """Copy audio file to generated directory"""
        try:
            # Generate unique filename
            timestamp = str(int(time.time()))
            audio_ext = audio_file_path.suffix
            new_filename = f"test_audio_{timestamp}{audio_ext}"
            destination_path = GENERATED_DIR / new_filename

            # Ensure generated directory exists
            GENERATED_DIR.mkdir(exist_ok=True)

            # Copy the file
            shutil.copy2(audio_file_path, destination_path)
            print(f"✅ Copied audio to: {destination_path}")

            return destination_path

        except Exception as e:
            print(f"❌ Failed to copy audio file: {e}")
            raise

    def get_available_images(self) -> List[GeneratedImage]:
        """Get available images from generated directory (limited to EXPECTED_IMAGES)"""
        images = []
        image_extensions = ['.png', '.jpg', '.jpeg']

        try:
            for file_path in GENERATED_DIR.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    # Extract age from filename if possible
                    filename = file_path.name
                    age = "25"  # default age

                    if "age_" in filename:
                        try:
                            age_part = filename.split("age_")[1].split("_")[0]
                            age = age_part
                        except:
                            pass

                    # Create GeneratedImage object
                    image = GeneratedImage(
                        url=f"/images/{filename}",
                        caption=f"Age {age}",
                        age=age,
                        year=f"Age {age}"
                    )
                    images.append(image)

            # Sort images by age if possible
            def sort_key(img):
                try:
                    return int(img.age)
                except:
                    return 0

            images.sort(key=sort_key)

            # Limit to EXPECTED_IMAGES
            limited_images = images[:EXPECTED_IMAGES]

            print(f"✅ Found {len(images)} images, using {len(limited_images)} for video generation")
            for img in limited_images:
                print(f"   - {img.url} (Age: {img.age})")

            if len(images) > EXPECTED_IMAGES:
                print(f"   ... and {len(images) - EXPECTED_IMAGES} more (not used)")

            return limited_images

        except Exception as e:
            print(f"❌ Error getting images: {e}")
            return []

    def create_sample_images(self) -> List[GeneratedImage]:
        """Create sample GeneratedImage objects for testing"""
        sample_images = [
            GeneratedImage(
                url="/images/base_age_20_1756387343.png",
                caption="Young adult at age 20",
                age="20",
                year="Age 20"
            ),
            GeneratedImage(
                url="/images/age_70_1756387399.png",
                caption="Elderly at age 70",
                age="70",
                year="Age 70"
            )
        ]

        # Verify images exist
        existing_images = []
        for img in sample_images:
            img_path = GENERATED_DIR / img.url.replace("/images/", "")
            if img_path.exists():
                existing_images.append(img)
                print(f"✅ Sample image available: {img_path.name}")
            else:
                print(f"⚠️  Sample image not found: {img_path.name}")

        return existing_images

    async def generate_video_with_audio(self, audio_file_path: Path, images: List[GeneratedImage]) -> str:
        """Generate video using Remotion with the uploaded audio"""
        try:
            print(f"\n🎬 Generating Video with Audio")
            print("-" * 40)
            print(f"Audio file: {audio_file_path.name}")
            print(f"Number of images: {len(images)}")

            # Use Remotion service to render video
            video_path = await self.remotion_service.render_video(
                images=images,
                audio_file=str(audio_file_path),
                title="Test Audio Video",
                name="Audio Test User",
                duration_per_image=2.0,
                transition_duration=0.5
            )

            print(f"✅ Video generated successfully: {video_path}")
            return video_path

        except Exception as e:
            print(f"❌ Video generation failed: {e}")
            raise

    async def run_audio_video_test(self):
        """Run the complete audio upload and video generation test"""
        print("🎵 Audio Upload & Video Generation Test Suite")
        print("=" * 60)
        print(f"Using audio file: {TEST_AUDIO_FILE}")
        print(f"Using {EXPECTED_IMAGES} images from generated folder")
        print()

        # Step 1: Get audio file
        try:
            audio_file_path = self.get_user_audio_file()
        except (FileNotFoundError, ValueError) as e:
            print(f"❌ Audio file error: {e}")
            self.log_test_result("Audio File Check", False, str(e))
            return
        except KeyboardInterrupt:
            print("\n⏹️  Test cancelled")
            return

        self.log_test_result("Audio File Check", True, f"Audio file validated: {audio_file_path.name}")

        # Step 2: Copy audio to generated directory
        try:
            copied_audio_path = self.copy_audio_to_generated(audio_file_path)
        except Exception as e:
            self.log_test_result("Audio Copy", False, f"Failed to copy audio file: {str(e)}")
            return

        self.log_test_result("Audio Copy", True, f"Successfully copied audio to generated directory")

        # Step 3: Get available images
        images = self.get_available_images()

        if not images:
            print("❌ No images found in generated directory. Please generate some images first.")
            self.log_test_result("Image Check", False, "No images available for video generation")
            return

        self.log_test_result("Image Check", True, f"Found {len(images)} images for video generation")

        # Step 4: Generate video with audio
        try:
            video_path = await self.generate_video_with_audio(copied_audio_path, images)
            self.log_test_result(
                "Video Generation",
                True,
                f"Successfully generated video with audio",
                {
                    "video_path": video_path,
                    "audio_file": copied_audio_path.name,
                    "image_count": len(images)
                }
            )
        except Exception as e:
            self.log_test_result(
                "Video Generation",
                False,
                f"Video generation failed: {str(e)}"
            )
            return

        # Step 5: Verify video file
        if os.path.exists(video_path):
            video_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
            self.log_test_result(
                "Video Verification",
                True,
                f"Video file created successfully ({video_size:.1f}MB)",
                {"file_path": video_path, "file_size_mb": video_size}
            )
        else:
            self.log_test_result("Video Verification", False, "Video file was not created")

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n📊 Test Summary")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")

        print("\n✅ Audio upload and video generation test completed!")

def main():
    """Main function"""
    print("🎵 TikTok Aging App - Audio Upload & Video Generation Test")
    print("This script will automatically:")
    print(f"1. Use the audio file: {TEST_AUDIO_FILE}")
    print(f"2. Copy it to the generated folder")
    print(f"3. Use {EXPECTED_IMAGES} images from the generated folder")
    print("4. Create a video using Remotion with your audio")
    print("5. Save the video to the generated folder")
    print()

    # Check if we're in the right directory
    if not Path("app/remotion_service.py").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)

    # Check if generated directory exists
    if not GENERATED_DIR.exists():
        print(f"⚠️  Generated directory not found: {GENERATED_DIR}")
        print("Creating it now...")
        GENERATED_DIR.mkdir(exist_ok=True)

    try:
        tester = AudioVideoTester()
        asyncio.run(tester.run_audio_video_test())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
