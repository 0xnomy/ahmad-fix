import os
import logging
import subprocess
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioProcessor:    
    def __init__(self):
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.aac']
    
    def validate_audio(self, file_path: str) -> Dict[str, any]:
        try:
            if not os.path.exists(file_path):
                return {'valid': False, 'error': 'File not found'}
            
            # Check file extension - be more robust
            file_ext = Path(file_path).suffix.lower()
            if not file_ext:
                # Try to extract extension from filename
                filename = os.path.basename(file_path)
                if '.' in filename:
                    file_ext = '.' + filename.split('.')[-1].lower()
                else:
                    return {'valid': False, 'error': 'No file extension found'}
            
            # Check if extension is supported
            if file_ext not in self.supported_formats:
                return {'valid': False, 'error': f'Unsupported format: {file_ext}. Supported formats: {self.supported_formats}'}
            
            # Check file size (max 50MB)
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB
                return {'valid': False, 'error': 'File too large (max 50MB)'}
            
            if file_size == 0:
                return {'valid': False, 'error': 'File is empty'}
            
            # Basic validation passed
            validation_result = {
                'valid': True,
                'format': file_ext,
                'size_mb': file_size / (1024 * 1024),
                'needs_conversion': file_ext != '.mp3'
            }
            
            logger.info(f"Audio validation passed: {validation_result}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Audio validation error for {file_path}: {str(e)}")
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    def convert_to_mp3(self, input_path: str, output_filename: str) -> Optional[str]:
        try:
            # Ensure uploads directory exists with absolute path
            backend_dir = Path(__file__).parent.parent.parent
            uploads_dir = backend_dir / "uploads"
            uploads_dir.mkdir(exist_ok=True)
            
            output_path = uploads_dir / output_filename
            
            # Check if input file exists and is readable
            input_file = Path(input_path)
            if not input_file.exists():
                logger.error(f"Input file does not exist: {input_path}")
                return None
                
            if not os.access(input_path, os.R_OK):
                logger.error(f"Input file is not readable: {input_path}")
                return None
            
            # Simple conversion using ffmpeg (requires ffmpeg to be installed)
            cmd = [
                'ffmpeg', '-i', str(input_path), 
                '-codec:a', 'mp3', 
                '-b:a', '128k',
                '-y',  # Overwrite output
                str(output_path)
            ]
            
            logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info(f"Successfully converted audio to: {output_path}")
                if output_path.exists():
                    return str(output_path)
                else:
                    logger.error(f"Conversion succeeded but output file not found: {output_path}")
                    return None
            else:
                logger.error(f"ffmpeg conversion failed: {result.stderr}")
                # If ffmpeg fails, just copy the file
                import shutil
                shutil.copy2(input_path, output_path)
                if output_path.exists():
                    logger.info(f"Copied original file to: {output_path}")
                    return str(output_path)
                else:
                    logger.error(f"Failed to copy file to: {output_path}")
                    return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"ffmpeg conversion timed out for: {input_path}")
            # Try to copy the file instead
            try:
                import shutil
                backend_dir = Path(__file__).parent.parent.parent
                uploads_dir = backend_dir / "uploads"
                output_path = uploads_dir / output_filename
                shutil.copy2(input_path, output_path)
                return str(output_path)
            except Exception as e:
                logger.error(f"File copy after timeout failed: {str(e)}")
                return None
        except FileNotFoundError:
            # ffmpeg not installed, just copy the file
            logger.warning("ffmpeg not found, copying file without conversion")
            try:
                import shutil
                backend_dir = Path(__file__).parent.parent.parent
                uploads_dir = backend_dir / "uploads"
                output_path = uploads_dir / output_filename
                shutil.copy2(input_path, output_path)
                return str(output_path)
            except Exception as e:
                logger.error(f"File copy failed: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Audio conversion error for {input_path}: {str(e)}")
            # Try to copy the file as a last resort
            try:
                import shutil
                backend_dir = Path(__file__).parent.parent.parent
                uploads_dir = backend_dir / "uploads"
                output_path = uploads_dir / output_filename
                shutil.copy2(input_path, output_path)
                return str(output_path)
            except Exception as copy_error:
                logger.error(f"Final file copy failed: {str(copy_error)}")
                return None
