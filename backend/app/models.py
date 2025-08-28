from pydantic import BaseModel
from typing import List, Optional
from fastapi import UploadFile

class VideoGenerationRequest(BaseModel):
    prompt: str
    num_images: int
    title: Optional[str] = "AI Generated Aging Journey"
    name: Optional[str] = "Generated Person"
    duration_per_image: Optional[float] = 2.0  # seconds per image
    transition_duration: Optional[float] = 0.5  # seconds for transitions

class GeneratedImage(BaseModel):
    url: str
    caption: str
    age: str
    year: str
    call_id: Optional[str] = None  
    base64_data: Optional[str] = None  

class VideoGenerationResponse(BaseModel):
    video_url: str
    images: List[GeneratedImage]
    audio_file: str
    generation_time: float
    video_duration: float  # total video duration in seconds

class IterativeAgingRequest(BaseModel):
    prompt: str
    start_age: int = 20
    end_age: int = 60
    age_increment: int = 20

class DynamicVideoRequest(BaseModel):
    prompt: str
    num_images: int = 3
    title: str = "My Story"
    name: str = "Through the Years"
    duration_per_image: float = 2.0
    transition_duration: float = 0.5
