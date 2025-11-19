import cv2
from pathlib import Path


FILE_NAME = r"Ella30"
INPUT_DIR = r"C:\\Presonal (Don't Enter)\\Personal\\Others\\EP"
OUTPUT_DIR = r"Enhanced"
INPUT_EXTENSION = r".jpg"
SCALE = 30.0  # Upscale by a factor of 2 (e.g., 2x)


def enhance_image_quality(input_image_path, output_image_path, scale_factor):
    """
    Enhance the quality of a colored image by upscaling and sharpening.

    Parameters:
        input_image_path (str): Path to the input image.
        output_image_path (str): Path to save the enhanced image.
        scale_factor (float): Factor by which to upscale the image.
    """
    # Read the image
    img = cv2.imread(input_image_path)
    if img is None:
        print(f"Error: Could not read the image at {input_image_path}")
        return

    # Convert to RGB (OpenCV loads images in BGR format by default)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Upscale the image using bicubic interpolation
    height, width = img.shape[:2]
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    upscaled_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    # Apply unsharp masking for sharpening
    # Create a Gaussian blurred version of the image
    blurred = cv2.GaussianBlur(upscaled_img, (5, 5), 1.5)
    sharpened = cv2.addWeighted(upscaled_img, 1.5, blurred, -0.5, 0)

    # Convert back to BGR for saving
    sharpened_bgr = cv2.cvtColor(sharpened, cv2.COLOR_RGB2BGR)

    # Save the enhanced image
    cv2.imwrite(output_image_path, sharpened_bgr)
    print(f"Enhanced image saved to {output_image_path}")

# ----------------------------
# MAIN
# ----------------------------
def main():
    input_path = Path(INPUT_DIR).joinpath(f"{FILE_NAME}{INPUT_EXTENSION}")  # Correctly formatted Windows path
    output_path = Path(INPUT_DIR).joinpath(OUTPUT_DIR).joinpath(f"{FILE_NAME}e.jpg")  # Save path

    enhance_image_quality(input_path, output_path, SCALE)


if __name__ == "__main__":
    main()
