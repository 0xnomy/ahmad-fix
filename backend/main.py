from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import asyncio
import os
import shutil
import time
import uuid
import logging
from datetime import datetime
from typing import Optional
import json
import re
from dotenv import load_dotenv

from app.models import VideoGenerationRequest, VideoGenerationResponse, GeneratedImage, DynamicVideoRequest
from app.openai_service import OpenAIService
from app.remotion_service import RemotionService
from app.audio_processor import AudioProcessor

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tiktok_aging_app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Create logger
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

app = FastAPI(
    title="TikTok Aging App API", 
    version="1.0.0",
    description="Long-running video generation API with proper timeout handling"
)

# Timeout middleware for long-running operations
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Handle timeouts for long-running video generation operations."""
    
    # Set different timeouts based on endpoint
    if "render" in request.url.path or "dynamic" in request.url.path:
        timeout = 900  # 15 minutes for video rendering
    elif "images" in request.url.path:
        timeout = 1200  # 20 minutes for image generation (GPT-5 can be slow)
    else:
        timeout = 60   # 1 minute for other operations
    
    try:
        start_time = time.time()
        response = await asyncio.wait_for(call_next(request), timeout=timeout)
        process_time = time.time() - start_time
        
        if process_time > 60:  # Log long operations
            logger.info(f"Long operation completed: {request.url.path} took {process_time:.2f}s")
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except asyncio.TimeoutError:
        logger.error(f"Request timeout after {timeout}s for {request.url.path}")
        raise HTTPException(
            status_code=504, 
            detail=f"Request timed out after {timeout} seconds. Video generation is still processing in background."
        )
    except Exception as e:
        logger.error(f"Middleware error for {request.url.path}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Trust localhost and development hosts
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "*.localhost"]
)

# CORS middleware - Updated for separate frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend running on port 3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for generated videos and images
app.mount("/generated", StaticFiles(directory="generated"), name="generated")
app.mount("/images", StaticFiles(directory="../public/images"), name="images")

# Initialize services
openai_service = OpenAIService()
remotion_service = RemotionService()
audio_processor = AudioProcessor()

@app.get("/status")
async def status_check():
    """Alternative status check endpoint"""
    return {"status": "healthy", "message": "TikTok Aging App API is running"}

@app.post("/dynamic-aging-video")
async def dynamic_aging_video(
    prompt: str = Form(...),
    num_images: int = Form(3),
    title: str = Form("My Aging Journey"),
    name: str = Form("Through the Years"),
    duration_per_image: float = Form(2.0),
    transition_duration: float = Form(0.5),
    audio_file: UploadFile = File(None)
):
    """
    NEW: Fully dynamic aging video generator that can handle ANY number of images
    - Dynamic age distribution (1-10+ images)
    - Configurable timing per image
    - Automatic video duration calculation
    - Supports custom audio
    """
    dynamic_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"[{dynamic_id}] DYNAMIC AGING VIDEO - Starting pipeline")
        logger.info(f"[{dynamic_id}] Config: {num_images} images, {duration_per_image}s each, {transition_duration}s transitions")
        logger.info(f"[{dynamic_id}] Prompt: '{prompt}', Title: '{title}', Name: '{name}'")
        
        # Validate inputs
        if num_images < 1 or num_images > 20:
            raise HTTPException(status_code=400, detail="Number of images must be between 1 and 20")
        if duration_per_image < 0.5 or duration_per_image > 10:
            raise HTTPException(status_code=400, detail="Duration per image must be between 0.5 and 10 seconds")
        if transition_duration < 0 or transition_duration > 3:
            raise HTTPException(status_code=400, detail="Transition duration must be between 0 and 3 seconds")
        
        # Calculate expected video duration
        expected_duration = (num_images * duration_per_image) + ((num_images - 1) * transition_duration) + 2  # +2 for intro/outro
        logger.info(f"[{dynamic_id}] Expected video duration: {expected_duration:.1f} seconds")
        
        # STEP 1: Generate images with dynamic age distribution
        logger.info(f"[{dynamic_id}] STEP 1: Generating {num_images} images with dynamic ages...")
        
        generated_images = await openai_service.generate_images_and_captions(prompt, num_images)
        successful_images = [img for img in generated_images if img.url]
        
        if len(successful_images) < 1:
            raise HTTPException(status_code=500, detail="No images were generated successfully")
        
        logger.info(f"[{dynamic_id}] Generated {len(successful_images)}/{num_images} images successfully")
        
        # STEP 2: Handle audio processing
        audio_path = None
        if audio_file and audio_file.filename != 'dummy.mp3' and audio_file.size > 0:
            timestamp = int(time.time())
            audio_filename = f"dynamic_audio_{timestamp}_{audio_file.filename}"
            audio_path = os.path.join("uploads", audio_filename)
            os.makedirs("uploads", exist_ok=True)
            
            with open(audio_path, "wb") as buffer:
                content = await audio_file.read()
                buffer.write(content)
            
            # Validate audio
            validation = audio_processor.validate_audio(audio_path)
            if not validation['valid']:
                os.remove(audio_path)
                logger.warning(f"[{dynamic_id}] Invalid audio file, proceeding without: {validation['error']}")
                audio_path = None
            else:
                logger.info(f"[{dynamic_id}] Audio uploaded and validated: {audio_filename}")
        
        # STEP 3: Render video with dynamic timing
        logger.info(f"[{dynamic_id}] STEP 2: Rendering video with dynamic timing...")
        
        video_path = await remotion_service.render_video(
            images=successful_images,
            audio_file=audio_path,
            title=title,
            name=name,
            duration_per_image=duration_per_image,
            transition_duration=transition_duration,
            text_transition_duration=1.0
        )
        
        # STEP 4: Calculate final metrics and return
        total_time = time.time() - start_time
        logger.info(f"[{dynamic_id}] PIPELINE COMPLETED in {total_time:.1f}s")
        
        response = {
            "success": True,
            "pipeline_id": dynamic_id,
            "total_time": total_time,
            "images_requested": num_images,
            "images_generated": len(successful_images),
            "video_url": f"/generated/{os.path.basename(video_path)}",
            "video_path": video_path,
            "expected_duration": expected_duration,
            "config": {
                "duration_per_image": duration_per_image,
                "transition_duration": transition_duration,
                "title": title,
                "name": name,
                "prompt": prompt
            },
            "images": [
                {
                    "url": f"/images/{img.url}",
                    "age": img.age,
                    "year": img.year,
                    "caption": img.caption
                }
                for img in successful_images
            ]
        }
        
        return response
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"[{dynamic_id}] Error in dynamic_aging_video: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dynamic video pipeline failed: {str(e)}")

@app.post("/regenerate-image")
async def regenerate_image(
    prompt: str = Form(...),
    age: int = Form(...),
    base_call_id: str = Form(None)
):
    """
    Regenerate a single image at a specific age
    """
    regen_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{regen_id}] Regenerating image for age {age} with prompt: {prompt}")
        logger.info(f"[{regen_id}] Base call ID: {base_call_id}")
        
        # Regenerate the image
        regenerated_image = await openai_service.regenerate_single_image(prompt, age, base_call_id)
        
        if regenerated_image:
            logger.info(f"[{regen_id}] Successfully regenerated image for age {age}")
            return {
                "success": True,
                "image": {
                    "url": f"/images/{regenerated_image.url}" if regenerated_image.url and not regenerated_image.url.startswith('/') else f"/images{regenerated_image.url}",
                    "caption": regenerated_image.caption,
                    "age": regenerated_image.age,
                    "year": regenerated_image.year
                }
            }
        else:
            logger.error(f"[{regen_id}] Failed to regenerate image for age {age}")
            return {
                "success": False,
                "error": "Failed to regenerate image"
            }
        
    except Exception as e:
        logger.error(f"[{regen_id}] Error in regenerate_image: {str(e)}")
        logger.error(f"[{regen_id}] Traceback:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/test-generate-images")
async def test_generate_images(
    prompt: str = Form(...),
    num_images: int = Form(3),
    custom_ages: str = Form(None)  # JSON string of custom ages
):
    """
    Generate images for testing/review purposes
    Returns images in format expected by frontend for review
    """
    test_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        logger.info(f"[{test_id}] Test Generate Images - Starting")
        logger.info(f"[{test_id}] Prompt: '{prompt}', Images: {num_images}")

        # Parse custom ages if provided
        custom_age_list = None
        if custom_ages:
            try:
                custom_age_list = json.loads(custom_ages)
                logger.info(f"[{test_id}] Using custom ages: {custom_age_list}")
            except json.JSONDecodeError as e:
                logger.warning(f"[{test_id}] Invalid custom_ages JSON: {e}")
                custom_age_list = None

        # Generate images using OpenAI service
        if custom_age_list:
            # Use GPT-5 iterative aging with custom ages
            generated_images = await openai_service.generate_images_and_captions(
                prompt=prompt,
                num_images=num_images,
                custom_ages=custom_age_list
            )
        else:
            # Use standard iterative aging
            generated_images = await openai_service.generate_images_and_captions(
                prompt=prompt,
                num_images=num_images
            )
        generation_time = time.time() - start_time

        logger.info(f"[{test_id}] Generated {len(generated_images)} images in {generation_time:.2f}s")

        # Convert GeneratedImage objects to frontend-expected format
        images_for_frontend = []
        successful_count = 0

        for img in generated_images:
            if img.url:
                # Create frontend-compatible image object
                frontend_image = {
                    'url': img.url,
                    'caption': img.caption or '',
                    'age': img.age or '',
                    'year': img.year or '',
                    'call_id': img.call_id or ''
                }
                images_for_frontend.append(frontend_image)
                successful_count += 1

        response_data = {
            'success': True,
            'images': images_for_frontend,
            'successful_images': successful_count,
            'total_images': len(generated_images),
            'generation_time': generation_time,
            'prompt': prompt,
            'num_images_requested': num_images
        }

        logger.info(f"[{test_id}] Test generation completed successfully")
        return response_data

    except Exception as e:
        logger.error(f"[{test_id}] Error in test_generate_images: {str(e)}")
        logger.error(f"[{test_id}] Traceback:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/gpt5-iterative-aging")
async def gpt5_iterative_aging(
    prompt: str = Form(...),
    ages: str = Form("20,40,60")  # Comma-separated ages
):
    """
    Generate images using GPT-5 iterative aging with custom ages
    """
    custom_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Parse ages
        age_list = [int(age.strip()) for age in ages.split(',')]
        if len(age_list) < 2:
            logger.warning(f"[{custom_id}] Invalid age list: {ages}")
            raise HTTPException(status_code=400, detail="At least 2 ages required")
        
        logger.info(f"[{custom_id}] GPT-5 Iterative Aging: {prompt}")
        logger.info(f"[{custom_id}] Target ages: {age_list}")
        
        # Generate images using OpenAI service
        generated_images = await openai_service.generate_images_and_captions(prompt, len(age_list))
        
        generation_time = time.time() - start_time
        logger.info(f"[{custom_id}] GPT-5 custom aging completed in {generation_time:.2f} seconds")
        
        # Calculate generation time
        generation_time = time.time() - start_time
        
        response = {
            "images": [
                {
                    "url": f"/images/{img.url}" if img.url and not img.url.startswith('/') else f"/images{img.url}",
                    "caption": img.caption,
                    "age": img.age,
                    "year": img.year,
                    "call_id": img.call_id if hasattr(img, 'call_id') else None
                }
                for img in generated_images
            ],
            "generation_time": generation_time,
            "total_images": len(generated_images),
            "successful_images": len([img for img in generated_images if img.url]),
            "workflow": "gpt5_iterative_aging",
            "target_ages": age_list
        }
        
        return response
        
    except Exception as e:
        print(f"❌ Error in gpt5_iterative_aging: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/render-aging-video")
async def render_aging_video(
    images_data: str = Form(...),  # JSON string of image data
    title: str = Form("AI Age Progression"),
    name: str = Form("Generated Person"),
    audio_file: UploadFile = File(None)
):
    """
    Render video from generated aging images using Remotion
    """
    render_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        import json
        
        logger.info(f"[{render_id}] Starting video render request")
        logger.info(f"[{render_id}] Title: '{title}', Name: '{name}'")
        
        # Parse images data
        images_json = json.loads(images_data)
        
        # Convert to GeneratedImage objects
        images = []
        for img_data in images_json:
            if img_data.get('url'):  # Only include successful images
                # Extract filename from URL (handle both full URLs and relative paths)
                url = img_data['url']
                if url.startswith('http'):
                    # Extract filename from full URL
                    filename = url.split('/')[-1]
                elif url.startswith('/images/'):
                    # Extract filename from relative path
                    filename = url.split('/')[-1]
                else:
                    filename = url
                
                image = GeneratedImage(
                    url=filename,  # Store just the filename
                    caption=img_data.get('caption', ''),
                    age=img_data.get('age', ''),
                    year=img_data.get('year', ''),
                    call_id=img_data.get('call_id')
                )
                images.append(image)
                logger.info(f"[{render_id}] Processed image: {url} -> {filename}")
        
        if len(images) < 2:
            logger.warning(f"[{render_id}] Insufficient images: {len(images)}")
            raise HTTPException(status_code=400, detail="At least 2 successful images required for video")
        
        logger.info(f"[{render_id}] Rendering video with {len(images)} images")
        
        # Handle audio file with processing and validation
        audio_path = None
        if audio_file and audio_file.filename != 'dummy.mp3':
            timestamp = int(time.time())
            original_filename = f"audio_{timestamp}_{audio_file.filename}"
            temp_audio_path = os.path.join("uploads", original_filename)
            os.makedirs("uploads", exist_ok=True)
            
            # Save uploaded file
            with open(temp_audio_path, "wb") as buffer:
                content = await audio_file.read()
                buffer.write(content)
            
            logger.info(f"[{render_id}] Audio uploaded: {temp_audio_path}")
            
            try:
                # Validate audio file
                validation = audio_processor.validate_audio(temp_audio_path)
                if not validation['valid']:
                    os.remove(temp_audio_path)  # Clean up
                    raise HTTPException(status_code=400, detail=f"Invalid audio file: {validation['error']}")
                
                logger.info(f"[{render_id}] Audio validation passed: {validation}")
                
                # Convert to MP3 if needed
                if validation.get('needs_conversion', False):
                    logger.info(f"[{render_id}] Converting audio to MP3...")
                    converted_path = audio_processor.convert_to_mp3(temp_audio_path, f"converted_{timestamp}.mp3")
                    audio_path = converted_path
                    os.remove(temp_audio_path)  # Clean up original
                    logger.info(f"[{render_id}] Audio converted successfully")
                else:
                    audio_path = temp_audio_path
                    logger.info(f"[{render_id}] Using original MP3 audio")
                    
            except Exception as e:
                logger.error(f"[{render_id}] Audio processing failed: {str(e)}")
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                raise HTTPException(status_code=400, detail=f"Audio processing failed: {str(e)}")
            
            print(f"🎵 Audio processed: {audio_path}")
        
        # Use default audio if none provided
        if not audio_path:
            # User requested to remove default audio - raise error if no audio provided
            raise HTTPException(
                status_code=400, 
                detail="No audio file provided. Please upload an audio file to create a video with sound."
            )
        
        # Render video using Remotion with dynamic timing
        print("🎬 Starting video rendering with Remotion...")
        
        # Calculate timing based on number of images (2 seconds per image)
        duration_per_image = 2.0
        transition_duration = 0.5
        
        video_path = await remotion_service.render_video(
            images, 
            audio_path, 
            title, 
            name,
            duration_per_image=duration_per_image,
            transition_duration=transition_duration,
            text_transition_duration=1.0
        )
        
        print(f"✅ Video rendered: {video_path}")
        
        # Calculate rendering time
        rendering_time = time.time() - start_time
        
        response = {
            "success": True,
            "video_url": f"/generated/{os.path.basename(video_path)}",
            "video_path": video_path,
            "rendering_time": rendering_time,
            "images_used": len(images),
            "title": title,
            "name": name,
            "audio_used": bool(audio_path)
        }
        
        return response
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"[{render_id}] Error in render_aging_video: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Video rendering failed: {str(e)}")

@app.post("/complete-aging-pipeline")
async def complete_aging_pipeline(
    prompt: str = Form(...),
    num_images: int = Form(3),
    title: str = Form("AI Age Progression"),
    name: str = Form("Generated Person"),
    audio_file: UploadFile = File(None)
):
    """
    Complete pipeline: Generate images + Create video in one go
    This is the full end-to-end workflow that users will experience
    """
    pipeline_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"[{pipeline_id}] Starting complete aging pipeline")
        logger.info(f"[{pipeline_id}] Prompt: '{prompt}', Images: {num_images}")
        logger.info(f"[{pipeline_id}] Video: '{title}' by '{name}'")
        
        # Step 1: Generate aging images using GPT-5 iterative workflow
        logger.info(f"[{pipeline_id}] Step 1: Generating {num_images} aging images...")

        generated_images = await openai_service.generate_images_and_captions(
            prompt=prompt,
            num_images=num_images
        )

        if not generated_images:
            raise HTTPException(status_code=500, detail="Image generation failed")

        logger.info(f"[{pipeline_id}] Generated {len(generated_images)} images successfully")
        
        # Step 2: Process images into GeneratedImage objects
        images = []
        for img_data in generated_images:
            if img_data.get('url'):
                # Extract filename from URL
                url = img_data['url']
                filename = url.split('/')[-1] if '/' in url else url
                
                image = GeneratedImage(
                    url=filename,  # Store just the filename
                    caption=img_data.get('caption', ''),
                    age=str(img_data.get('age', '')),
                    year=str(img_data.get('year', img_data.get('age', ''))),
                    call_id=img_data.get('call_id')
                )
                images.append(image)
        
        if len(images) < 2:
            raise HTTPException(status_code=400, detail="At least 2 successful images required for video")
        
        # Step 3: Handle audio file
        audio_path = None
        if audio_file and audio_file.filename != 'dummy.mp3' and audio_file.size > 0:
            timestamp = int(time.time())
            audio_filename = f"pipeline_audio_{timestamp}_{audio_file.filename}"
            audio_path = os.path.join("uploads", audio_filename)
            os.makedirs("uploads", exist_ok=True)
            
            with open(audio_path, "wb") as buffer:
                content = await audio_file.read()
                buffer.write(content)
            
            logger.info(f"[{pipeline_id}] Custom audio uploaded: {audio_filename}")
        
        # Use default audio if none provided
        if not audio_path:
            # User requested to remove default audio - raise error if no audio provided
            raise HTTPException(
                status_code=400, 
                detail="No audio file provided. Please upload an audio file to create a video with sound."
            )
        
        # Step 4: Render video using Remotion with dynamic timing
        logger.info(f"[{pipeline_id}] Step 2: Rendering video with {len(images)} images...")
        
        # Calculate dynamic timing: 2 seconds per image
        duration_per_image = 2.0
        transition_duration = 0.5
        
        video_path = await remotion_service.render_video(
            images, 
            audio_path, 
            title, 
            name,
            duration_per_image=duration_per_image,
            transition_duration=transition_duration,
            text_transition_duration=1.0
        )
        
        # Step 5: Calculate total time and return results
        total_time = time.time() - start_time
        
        logger.info(f"[{pipeline_id}] Pipeline completed successfully in {total_time:.1f}s")
        
        response = {
            "success": True,
            "pipeline_id": pipeline_id,
            "total_time": total_time,
            "image_generation_time": 0,  # TODO: Track image generation time separately
            "video_rendering_time": total_time,
            "images_generated": len(images),
            "video_url": f"/generated/{os.path.basename(video_path)}",
            "video_path": video_path,
            "title": title,
            "name": name,
            "prompt": prompt,
            "images": [
                {
                    "url": f"/images/{img.url}",
                    "age": img.age,
                    "year": img.year,
                    "caption": img.caption
                }
                for img in images
            ]
        }
        
        return response
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"[{pipeline_id}] Error in complete pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Complete pipeline failed: {str(e)}")

@app.post("/generate-and-render-video")
async def generate_and_render_video(
    prompt: str = Form(...),
    num_images: int = Form(3),
    title: str = Form("AI Age Progression"),
    name: str = Form("Generated Person"),
    audio_file: UploadFile = File(None)
):
    """
    Complete workflow: Generate images with GPT-5 iterative aging AND render video
    """
    start_time = time.time()
    
    try:
        print(f"🚀 Complete Workflow: Generate + Render Video")
        print(f"📝 Prompt: {prompt}")
        print(f"🎯 Images: {num_images}, Title: {title}, Name: {name}")
        
        # Step 1: Generate images
        print("🎨 Step 1: Generating images with GPT-5 iterative aging...")
        generated_images = await openai_service.generate_images_and_captions(prompt, num_images)
        
        # Filter successful images
        successful_images = [img for img in generated_images if img.url]
        
        if len(successful_images) < 2:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough successful images generated. Got {len(successful_images)}, need at least 2"
            )
        
        print(f"✅ Step 1 Complete: Generated {len(successful_images)} successful images")
        
        # Step 2: Handle audio
        audio_path = None
        if audio_file and audio_file.filename != 'dummy.mp3':
            timestamp = int(time.time())
            audio_filename = f"audio_{timestamp}_{audio_file.filename}"
            audio_path = os.path.join("uploads", audio_filename)
            os.makedirs("uploads", exist_ok=True)
            
            with open(audio_path, "wb") as buffer:
                content = await audio_file.read()
                buffer.write(content)
            
            print(f"🎵 Audio uploaded: {audio_path}")
        else:
            # User requested to remove default audio - require audio file
            raise HTTPException(
                status_code=400, 
                detail="No audio file provided. Please upload an audio file to create a video with sound."
            )
        
        # Step 3: Render video with dynamic timing
        print("🎬 Step 2: Rendering video with Remotion...")
        
        # Use default timing but allow for dynamic expansion
        duration_per_image = 2.0
        transition_duration = 0.5
        
        video_path = await remotion_service.render_video(
            successful_images, 
            audio_path, 
            title, 
            name,
            duration_per_image=duration_per_image,
            transition_duration=transition_duration,
            text_transition_duration=1.0
        )
        
        print(f"✅ Step 2 Complete: Video rendered successfully")
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Return complete response
        response = {
            "success": True,
            "video_url": f"/generated/{os.path.basename(video_path)}",
            "video_path": video_path,
            "images": [
                {
                    "url": f"/images/{img.url}" if img.url and not img.url.startswith('/') else f"/images{img.url}",
                    "caption": img.caption,
                    "age": img.age,
                    "year": img.year,
                    "call_id": img.call_id if hasattr(img, 'call_id') else None
                }
                for img in generated_images
            ],
            "total_time": total_time,
            "images_generated": len(generated_images),
            "successful_images": len(successful_images),
            "title": title,
            "name": name,
            "workflow": "gpt5_iterative_aging_plus_video",
            "audio_used": bool(audio_path)
        }
        
        return response
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error in generate_and_render_video: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Complete workflow failed: {str(e)}")

@app.post("/generate-video", response_model=VideoGenerationResponse)
async def generate_video(
    prompt: str = Form(...),
    num_images: int = Form(...),
    title: str = Form("AI Generated Journey"),
    name: str = Form("Generated Person"),
    images_data: str = Form(...),  # JSON string of accepted images
    audio_file: Optional[UploadFile] = File(None)  # Make audio optional
):
    """
    Generate a video with AI-generated images based on the prompt
    Audio is optional - will use default if not provided
    """
    start_time = time.time()

    try:
        # Validate inputs
        if num_images < 2 or num_images > 10:
            raise HTTPException(status_code=400, detail="Number of images must be between 2 and 10")

        # Parse images data
        try:
            accepted_images = json.loads(images_data)
            print(f"Received {len(accepted_images)} images from frontend")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid images_data format: {str(e)}")

        if len(accepted_images) < 2:
            raise HTTPException(status_code=400, detail="At least 2 images required for video generation")

        # Handle audio file (now optional)
        audio_path = None
        audio_filename = ""
        if audio_file and audio_file.filename:
            print(f"Processing audio file: {audio_file.filename}, size: {getattr(audio_file, 'size', 'unknown')}")

            # Save uploaded audio file temporarily for validation
            temp_audio_filename = f"temp_{uuid.uuid4().hex[:8]}_{audio_file.filename}"
            temp_audio_path = os.path.join("uploads", temp_audio_filename)

            os.makedirs("uploads", exist_ok=True)

            with open(temp_audio_path, "wb") as buffer:
                shutil.copyfileobj(audio_file.file, buffer)

            print(f"Temporary audio file saved: {temp_audio_path}")

            # Validate audio file using AudioProcessor
            validation = audio_processor.validate_audio(temp_audio_path)
            print(f"Audio validation result: {validation}")

            if not validation['valid']:
                os.remove(temp_audio_path)  # Clean up temp file
                raise HTTPException(status_code=400, detail=f"Invalid audio file: {validation['error']}")

            print(f"Audio validation passed: {validation}")

            # Convert to MP3 if needed
            if validation['needs_conversion']:
                print("Converting audio to MP3...")
                converted_filename = f"converted_{uuid.uuid4().hex[:8]}.mp3"
                converted_path = audio_processor.convert_to_mp3(temp_audio_path, converted_filename)
                if converted_path:
                    audio_path = converted_path
                    audio_filename = converted_filename
                    os.remove(temp_audio_path)  # Clean up temp file
                    print(f"Audio converted successfully: {converted_path}")
                else:
                    os.remove(temp_audio_path)  # Clean up temp file
                    raise HTTPException(status_code=500, detail="Failed to convert audio file")
            else:
                # No conversion needed, use original file
                audio_filename = f"{uuid.uuid4().hex[:8]}_{audio_file.filename}"
                audio_path = os.path.join("uploads", audio_filename)
                os.rename(temp_audio_path, audio_path)
                print(f"Audio file ready (no conversion needed): {audio_path}")

            print(f"Final audio file: {audio_path}")

        else:
            print("No audio file provided - will use default audio")

        # Use default audio if none provided
        if not audio_path:
            # User requested to remove default audio - require audio file
            raise HTTPException(
                status_code=400, 
                detail="No audio file provided. Please upload an audio file to create a video with sound."
            )

        # Use the accepted images instead of generating new ones
        print(f"Using {len(accepted_images)} accepted images for video")

        # Convert dictionaries to GeneratedImage objects
        successful_images = []
        for img_data in accepted_images:
            if isinstance(img_data, dict) and 'url' in img_data:
                img_obj = GeneratedImage(
                    url=img_data['url'],
                    caption=img_data.get('caption', ''),
                    age=str(img_data.get('age', '')),
                    year=str(img_data.get('year', '')),
                    call_id=img_data.get('call_id'),
                    base64_data=img_data.get('base64_data')
                )
                successful_images.append(img_obj)
            else:
                print(f"Skipping invalid image data: {img_data}")

        if len(successful_images) < 2:
            raise HTTPException(status_code=400, detail="At least 2 valid images required for video generation")

        print(f"Converted {len(successful_images)} images to GeneratedImage objects")

        # Render video using Remotion
        print("Starting video rendering with Remotion...")
        video_path = await remotion_service.render_video(
            successful_images, 
            audio_path, 
            title, 
            name,
            duration_per_image=2.0,
            transition_duration=0.5,
            text_transition_duration=1.0
        )

        print(f"Video rendered: {video_path}")

        # Calculate generation time
        generation_time = time.time() - start_time

        # Return response
        response = VideoGenerationResponse(
            video_url=f"/generated/{os.path.basename(video_path)}",
            images=successful_images,
            audio_file=audio_filename,
            generation_time=generation_time
        )

        return response

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in generate_video: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/download-video/{filename}")
async def download_video(filename: str):
    """
    Download the generated video file
    """
    file_path = os.path.join("generated", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        path=file_path,
        media_type='video/mp4',
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    # Check if required directories exist
    directories = {
        "generated": os.path.exists("generated"),
        "uploads": os.path.exists("uploads"),
        "public": os.path.exists("../public"),
        "public_images": os.path.exists("../public/images")
    }
    
    # Create missing directories
    os.makedirs("generated", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("../public/images", exist_ok=True)
    
    return {
        "status": "healthy",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "remotion_path": os.getenv("REMOTION_PROJECT_PATH", "../"),
        "directories": directories,
        "workflow": "step_by_step_enabled"
    }

# Backend API only - no frontend serving
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
