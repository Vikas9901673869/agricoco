from pathlib import Path
import sys

# Get the absolute path of the current file
file_path = Path(__file__).resolve()

# Root directory
root_path = file_path.parent
if root_path not in sys.path:
    sys.path.append(str(root_path))

# Images config
IMAGE = 'Image'
SOURCES_LIST = [IMAGE]

# Default sample images
IMAGES_DIR = root_path / 'images'
DEFAULT_IMAGE = IMAGES_DIR / 'test.jpg'
DEFAULT_DETECT_IMAGE = IMAGES_DIR / 'detected.jpg'

# ML Model Config
MODEL_DIR = root_path / 'weights'
DETECTION_MODEL = MODEL_DIR / 'best.pt'