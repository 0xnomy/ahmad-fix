import subprocess
import os
import json
import shutil
import logging
import time
import uuid
from pathlib import Path
from typing import List
from app.models import GeneratedImage
import sys

# Configure logging
logger = logging.getLogger(__name__)

# Use the same directory constants as main.py
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent   # backend/..
GENERATED_DIR = BASE_DIR / "generated"
UPLOADS_DIR = BASE_DIR / "uploads"

class RemotionService:
    def __init__(self):
        self.project_path = os.getenv("REMOTION_PROJECT_PATH", "../")
        self.project_path = os.path.abspath(self.project_path)
        self.generated_dir = GENERATED_DIR
        # Ensure directories exist
        self.generated_dir.mkdir(parents=True, exist_ok=True)

        # Debug logging
        logger.info(f"RemotionService initialized:")
        logger.info(f"  BASE_DIR: {BASE_DIR}")
        logger.info(f"  GENERATED_DIR: {GENERATED_DIR}")
        logger.info(f"  UPLOADS_DIR: {UPLOADS_DIR}")
        logger.info(f"  self.generated_dir: {self.generated_dir}")
        logger.info(f"  project_path: {self.project_path}")
        
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL like http://localhost:8000/images/aged_40_1756232627.png"""
        if url.startswith('http://') or url.startswith('https://'):
            return url.split('/')[-1]
        elif url.startswith('/images/'):
            return url.replace('/images/', '')
        else:
            return url
            
    def _copy_images_to_public(self, images: List[GeneratedImage]) -> List[dict]:
        """Copy generated images to public/images directory and return proper data structure"""
        copied_images = []

        # Ensure public/images directory exists
        public_images_dir = os.path.join(self.project_path, "public", "images")
        os.makedirs(public_images_dir, exist_ok=True)

        for img in images:
            if not img.url:
                continue

            try:
                # Extract filename from URL
                filename = self._extract_filename_from_url(img.url)

                # Source path (in generated/ - using unified path)
                source_path = self.generated_dir / filename

                # Destination path (in public/images/)
                dest_path = os.path.join(public_images_dir, filename)

                if source_path.exists():
                    # Copy image to public/images/
                    shutil.copy2(str(source_path), dest_path)
                    logger.info(f"Image copied: {filename}")

                    # Create proper data structure for Remotion (matching aged-reel-data.ts)
                    photo_data = {
                        "year": img.year or f"Age {img.age}",
                        "age": img.age,
                        "image": f"images/{filename}"  # Relative path for Remotion
                    }
                    copied_images.append(photo_data)
                else:
                    logger.warning(f"Image not found: {source_path}")

            except Exception as e:
                logger.error(f"Error processing image {img.url}: {e}")
                continue

        return copied_images

    async def render_video(self, images: List[GeneratedImage], audio_file: str, title: str, name: str, duration_per_image: float = 2.0, transition_duration: float = 0.5, text_transition_duration: float = 1.0) -> str:
        """Complete pipeline: Copy images, setup audio, render video with Remotion with dynamic timing"""
        
        video_id = str(int(time.time()))
        
        try:
            logger.info(f"[{video_id}] Starting dynamic video pipeline")
            logger.info(f"[{video_id}] Title: '{title}', Name: '{name}', Images: {len(images)}")
            logger.info(f"[{video_id}] Timing: {duration_per_image}s per image, {transition_duration}s transitions")
            
            # Step 1: Copy images to public directory and get proper data structure
            photos_data = self._copy_images_to_public(images)
            
            if len(photos_data) < 1:
                raise Exception(f"No valid images found: {len(photos_data)}. Need at least 1.")
            
            logger.info(f"[{video_id}] Copied {len(photos_data)} images to generated/")
            
            # Step 2: Handle audio file
            if not audio_file or not os.path.exists(audio_file):
                raise Exception("Audio file is required for video generation. Please provide a valid audio file.")
            
            try:
                # Copy audio to public directory
                public_audio_dir = os.path.join(self.project_path, "public")
                os.makedirs(public_audio_dir, exist_ok=True)
                
                # Generate unique audio filename
                audio_ext = os.path.splitext(audio_file)[1]
                audio_filename = f"custom_audio_{video_id}{audio_ext}"
                public_audio_path = os.path.join(public_audio_dir, audio_filename)
                
                shutil.copy2(audio_file, public_audio_path)
                logger.info(f"[{video_id}] Copied custom audio: {audio_filename}")
            except Exception as e:
                raise Exception(f"Failed to process audio file: {e}")
            
            # Step 3: Create dynamic Remotion props data (matching new AgedReelProps interface)
            remotion_props = {
                "title": title,
                "name": name,
                "audioFile": audio_filename,  # Just filename, not public/filename
                "images": photos_data,  # Changed from "years" to "images"
                "durationPerImage": duration_per_image,  # Dynamic: seconds per image
                "transitionDuration": transition_duration,  # Dynamic: transition duration
                "textTransitionDuration": text_transition_duration  # Text fade-in duration
            }
            
            logger.info(f"[{video_id}] Created dynamic props for {len(photos_data)} photos")
            logger.info(f"[{video_id}] Video will be ~{len(photos_data) * duration_per_image + (len(photos_data)-1) * transition_duration:.1f} seconds long")
            
            # Step 4: Create props file with absolute path
            props_filename = f"video_props_{uuid.uuid4().hex[:8]}.json"
            props_file_path = os.path.abspath(os.path.join("generated", props_filename))
            
            # Ensure generated directory exists
            os.makedirs("generated", exist_ok=True)
            
            # Write props file with pretty formatting
            with open(props_file_path, 'w', encoding='utf-8') as f:
                json.dump(remotion_props, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[{video_id}] Created props file: {props_file_path}")
            
            # Step 5: Generate output video path
            output_filename = f"aging_video_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.abspath(os.path.join(self.project_path, "generated", output_filename))
            
            # Step 6: Build Remotion render command with timeout configurations
            cmd = [
                "npx", "remotion", "render",
                "src/index.ts",  # Entry point
                "DynamicAgedReel",      # Component name
                output_path,     # Output file
                f"--props={props_file_path}",  # Props file path
                "--overwrite",
                "--log=verbose",
                "--timeout=120000",  # 2 minutes total timeout (milliseconds)
                "--delay-render-timeout=10000",  # 10 seconds for delayRender (milliseconds)
                "--concurrency=1",  # Single thread to avoid issues
                "--gl=swangle",  # Use software rendering instead of EGL
            ]
            
            # Use .cmd on Windows
            if sys.platform.startswith('win'):
                cmd[0] = "npx.cmd"
            
            logger.info(f"[{video_id}] Executing Remotion render...")
            logger.info(f"[{video_id}] Command: {' '.join(cmd)}")
            logger.info(f"[{video_id}] Working directory: {self.project_path}")
            
            # Step 7: Execute Remotion render with extended timeout
            # Dynamic timeout based on number of images (more images = longer render time)
            base_timeout = 120  # 2 minutes base
            per_image_timeout = 30  # 30 seconds per image
            max_timeout = 300  # 5 minutes maximum
            
            estimated_timeout = min(base_timeout + (len(photos_data) * per_image_timeout), max_timeout)
            
            logger.info(f"[{video_id}] Using timeout: {estimated_timeout}s for {len(photos_data)} images")
            
            process = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                shell=False,
                timeout=estimated_timeout
            )
            
            # Step 8: Handle render results
            if process.returncode == 0:
                logger.info(f"[{video_id}] Video rendered successfully!")
                logger.info(f"[{video_id}] Output: {output_path}")
                
                # Clean up props file
                try:
                    os.remove(props_file_path)
                except:
                    pass
                
                return output_path
            else:
                # Log detailed error information
                logger.error(f"[{video_id}] Remotion render failed with return code {process.returncode}")
                logger.error(f"[{video_id}] STDOUT: {process.stdout}")
                logger.error(f"[{video_id}] STDERR: {process.stderr}")
                
                # Clean up on failure
                try:
                    os.remove(props_file_path)
                except:
                    pass
                
                raise Exception(f"Remotion render failed: {process.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"[{video_id}] Render timeout after {estimated_timeout} seconds")
            raise Exception(f"Video rendering timed out after {estimated_timeout} seconds. This may be due to complex images or system performance. Try using fewer images or simpler content.")
        except Exception as e:
            logger.error(f"[{video_id}] Error in video pipeline: {str(e)}")
            raise e
