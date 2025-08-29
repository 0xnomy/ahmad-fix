import os
import base64
import time
import logging
from openai import OpenAI
from typing import List, Optional
from app.models import GeneratedImage
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)

    def _create_safe_prompt(self, base_prompt: str, age: int, is_base: bool = True, age_difference: int = 0) -> str:
        """Create a flexible prompt that incorporates the user's original request."""
        # Clean and enhance the base prompt
        clean_prompt = base_prompt.strip()

        if is_base:
            # For the base image, use the user's prompt with age context
            return f"{clean_prompt}, person aged {age} years old, natural lighting, high quality"
        else:
            # For progression images, modify the original prompt with age difference
            return f"{clean_prompt}, same person but {age_difference} years older (now aged {age}), natural aging progression, natural lighting, high quality"

    async def generate_images_and_captions(self, prompt: str, num_images: int, custom_ages: List[int] = None, starting_age: int = 20, age_gap: int = 15) -> List[GeneratedImage]:
        generated_images = []
        
        # Use custom ages if provided, otherwise use dynamic age calculation
        if custom_ages:
            ages = custom_ages
        elif starting_age and age_gap:
            # Generate ages based on starting age and gap
            ages = [starting_age + (i * age_gap) for i in range(num_images)]
        else:
            # Default dynamic age calculation based on number of images
            if num_images == 1:
                ages = [25]
            elif num_images == 2:
                ages = [20, 60]
            elif num_images == 3:
                ages = [20, 40, 60]
            elif num_images == 4:
                ages = [20, 35, 50, 65]
            elif num_images == 5:
                ages = [20, 30, 40, 50, 60]
            elif num_images == 6:
                ages = [20, 30, 40, 50, 60, 70]
            elif num_images == 7:
                ages = [20, 25, 35, 45, 55, 65, 75]
            elif num_images == 8:
                ages = [20, 25, 35, 45, 55, 65, 75, 85]
            elif num_images == 9:
                ages = [20, 25, 30, 40, 50, 60, 70, 80, 90]
            else:  # 10 or more images
                # Calculate ages evenly distributed from 20 to 90
                age_range = 90 - 20
                age_increment = age_range / (num_images - 1)
                ages = [int(20 + i * age_increment) for i in range(num_images)]
        
        logger.info(f"Generating {len(ages)} images for ages: {ages}")
        logger.info(f"Starting GPT-5 image generation workflow")
        
        base_age = ages[0]
        # Create a professional, context-rich prompt
        safe_base_prompt = self._create_safe_prompt(prompt, base_age, is_base=True)
        
        logger.info(f"Step 1: Generating base image for age {base_age}")
        logger.debug(f"Base prompt: {safe_base_prompt}")
        
        logger.info("Calling GPT-5 responses API for base image...")
        start_time = time.time()
        
        try:
            base_response = self.client.responses.create(
                model="gpt-5",
                input=safe_base_prompt,
                tools=[{"type": "image_generation"}],
            )
        except Exception as e:
            logger.error(f"GPT-5 base generation failed: {str(e)}")
            raise
        
        duration = time.time() - start_time
        logger.info(f"Base generation completed in {duration:.1f} seconds")
        logger.info(f"Response ID: {base_response.id}")
        
        base_image_calls = [
            output for output in base_response.output
            if output.type == "image_generation_call"
        ]
        
        if not base_image_calls:
            logger.error("No image generation calls found in base response")
            raise ValueError("Failed to generate base image - no image data returned")
        
        base_image_data = base_image_calls[0].result
        base_response_id = base_response.id
        
        logger.info("Base image generated successfully!")
        logger.debug(f"Image data length: {len(base_image_data):,} characters")
        
        # Save base image
        base_filename = f"base_age_{base_age}_{int(time.time())}.png"
        base_path = await self._save_base64_image(base_image_data, base_filename)
        
        if not base_path:
            logger.error("Failed to save base image")
            raise ValueError("Failed to save base image to disk")
        
        base_image = GeneratedImage(
            url=base_path,
            caption=f"Age {base_age}",
            age=f"{base_age} Years Old",
            year=str(2025),  # Current year as baseline
            call_id=base_response_id,
            base64_data=base_image_data
        )
        generated_images.append(base_image)
        logger.info(f"Step 1 Complete: Base image saved for age {base_age}")
        
        previous_response_id = base_response_id
        
        # Generate subsequent images with professional context
        for i in range(1, len(ages)):
            current_age = ages[i]
            age_difference = current_age - ages[i-1]
            
            # Create professional prompt for this age
            safe_age_prompt = self._create_safe_prompt(prompt, current_age, is_base=False, age_difference=age_difference)
            
            logger.info(f"Step {i+1}: Generating image {i+1} of {len(ages)}")
            logger.info(f"Previous Response ID: {previous_response_id}")
            logger.debug(f"Prompt: {safe_age_prompt}")
            
            logger.info("Calling GPT-5 with previous response...")
            start_time = time.time()
            
            try:
                age_response = self.client.responses.create(
                    model="gpt-5",
                    previous_response_id=previous_response_id,
                    input=safe_age_prompt,
                    tools=[{"type": "image_generation"}],
                )
            except Exception as e:
                logger.error(f"Safety system rejected generation for age {current_age}: {str(e)}")
                # Skip this age and continue with next one
                continue
            
            duration = time.time() - start_time
            logger.info(f"Age generation took {duration:.1f} seconds")
            logger.info(f"New Response ID: {age_response.id}")
            
            age_image_calls = [
                output for output in age_response.output
                if output.type == "image_generation_call"
            ]
            
            if age_image_calls:
                age_image_data = age_image_calls[0].result
                age_filename = f"age_{current_age}_{int(time.time())}.png"
                age_path = await self._save_base64_image(age_image_data, age_filename)
                
                if age_path:
                    age_image = GeneratedImage(
                        url=age_path,
                        caption=f"Age {current_age}",
                        age=f"{current_age} Years Old",
                        year=str(2025 + (current_age - base_age)),  # Simulate time passage
                        call_id=age_response.id,
                        base64_data=age_image_data
                    )
                    generated_images.append(age_image)
                    logger.info(f"Step {i+1} Complete: Image saved for age {current_age}")
                    
                    previous_response_id = age_response.id
                else:
                    logger.error(f"Failed to save image for age {current_age}")
                    continue
            else:
                logger.error(f"No image data found for age {current_age}")
                continue
                
            # Small delay between requests
            await asyncio.sleep(0.5)  # Reduced delay to avoid rate limiting
        
        logger.info(f"Generated {len(generated_images)} images total")
        return generated_images

    async def regenerate_single_image(self, original_prompt: str, age: int, base_call_id: Optional[str] = None) -> Optional[GeneratedImage]:
        logger.info(f"Regenerating image for age {age}")
        
        safe_age_prompt = self._create_safe_prompt(original_prompt, age, is_base=(base_call_id is None), age_difference=0)
        
        try:
            if base_call_id and age > 20:
                # Use progression from base image
                response = self.client.responses.create(
                    model="gpt-5",
                    previous_response_id=base_call_id,
                    input=safe_age_prompt,
                    tools=[{"type": "image_generation"}]
                )
            else:
                # Generate new base image for this age
                response = self.client.responses.create(
                    model="gpt-5",
                    input=safe_age_prompt,
                    tools=[{"type": "image_generation"}]
                )
        except Exception as e:
            logger.error(f"Regeneration failed for age {age}: {str(e)}")
            return None
        
        image_calls = [
            output for output in response.output
            if output.type == "image_generation_call"
        ]
        
        if image_calls:
            image_data = image_calls[0].result
            filename = f"regen_age_{age}_{int(time.time())}.png"
            local_image_path = await self._save_base64_image(image_data, filename)
            
            if local_image_path:
                logger.info(f"Successfully regenerated image for age {age}")
                return GeneratedImage(
                    url=local_image_path,
                    caption=f"Age {age}",
                    age=f"{age} Years Old",
                    year=str(2025),  # Current year as baseline
                    call_id=response.id,
                    base64_data=image_data
                )
        
        logger.error(f"Failed to regenerate image for age {age}")
        return None

    def _extract_start_age(self, prompt: str) -> int:
        words = prompt.lower().split()
        for i, word in enumerate(words):
            if word in ["age", "from"] and i + 1 < len(words):
                try:
                    return int(words[i + 1])
                except ValueError:
                    continue
        return 20

    def _extract_end_age(self, prompt: str) -> int:
        """Extract ending age from prompt text."""
        words = prompt.lower().split()
        for i, word in enumerate(words):
            if word == "to" and i + 1 < len(words):
                try:
                    return int(words[i + 1])
                except ValueError:
                    continue
        return 60

    async def _save_base64_image(self, base64_data: str, filename: str) -> str:
        try:
            from pathlib import Path
            image_bytes = base64.b64decode(base64_data)

            # Use unified directory constants (same as main.py)
            BASE_DIR = Path(__file__).resolve().parent.parent.parent   # backend/..
            GENERATED_DIR = BASE_DIR / "generated"
            GENERATED_DIR.mkdir(parents=True, exist_ok=True)

            file_path = GENERATED_DIR / filename
            with open(file_path, 'wb') as f:
                f.write(image_bytes)

            logger.info(f"Image saved successfully: {file_path}")
            # Return the full path for frontend access through static mount
            return f"/generated/{filename}"

        except Exception as e:
            logger.error(f"Error saving image {filename}: {str(e)}")
            return ""