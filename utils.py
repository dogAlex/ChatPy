import base64
import io
from PIL import Image

def validate_image(file_data):
    """Validate uploaded image and convert to base64."""
    # Check file size (max 5MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if len(file_data) > MAX_FILE_SIZE:
        return None, "File size too large (max 5MB)"
    
    try:
        # Validate image format
        img = Image.open(io.BytesIO(file_data))
        if img.format not in ['JPEG', 'PNG', 'GIF']:
            return None, "Unsupported format. Please upload JPG, PNG or GIF"
        
        # Resize if too large
        MAX_SIZE = (800, 800)
        if img.size[0] > MAX_SIZE[0] or img.size[1] > MAX_SIZE[1]:
            img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format=img.format)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/{img.format.lower()};base64,{img_str}", None
        
    except Exception as e:
        return None, f"Error processing image: {str(e)}"
