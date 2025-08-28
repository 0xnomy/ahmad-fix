import asyncio
import os
import sys
from app.remotion_service import RemotionService
from app.models import GeneratedImage

async def test_video_generation():
    """Test video generation using existing images in generated/"""

    # Initialize the service
    service = RemotionService()

    # Create test images based on existing files
    test_images = [
        GeneratedImage(
            url="/images/base_age_20_1756360221.png",
            caption="Starting young",
            age="20",
            year="Age 20"
        ),
        GeneratedImage(
            url="/images/age_70_1756360331.png",
            caption="Growing older",
            age="70",
            year="Age 70"
        )
    ]

    # Test parameters
    audio_file = "../uploads/aud_0.mp3"  # Use existing audio file
    title = "Test Aging Video with Audio"
    name = "Test Person"
    duration_per_image = 2.0
    transition_duration = 0.5

    try:
        print("Starting video generation test...")
        print(f"Images: {len(test_images)}")
        print(f"Title: {title}")
        print(f"Name: {name}")

        # Generate the video
        video_path = await service.render_video(
            images=test_images,
            audio_file=audio_file,
            title=title,
            name=name,
            duration_per_image=duration_per_image,
            transition_duration=transition_duration
        )

        print(f"✅ Video generated successfully!")
        print(f"📁 Output path: {video_path}")

        # Check if file exists
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            print(f"📊 File size: {file_size} bytes")
        else:
            print("❌ Video file not found!")

    except Exception as e:
        print(f"❌ Error during video generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_video_generation())
