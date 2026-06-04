# Rename all image files in the images directory to have a consistent naming convention (e.g., lowercase with hyphens instead of spaces, image-001.jpg, image-002.jpg, etc.)
#Takes input from the user for the directory containing the images and renames all image files in that directory according to the specified naming convention. The script will print out the old and new file names for each renamed file.
import os

image_dir = input("Enter the path to the directory containing the images: ")
for i, filename in enumerate(os.listdir(image_dir), start=1):
    if filename.endswith((".jpg", ".jpeg", ".png")):
        old_path = os.path.join(image_dir, filename)
        new_filename = f"image-{i:03d}{os.path.splitext(filename)[1]}"
        new_path = os.path.join(image_dir, new_filename)
        os.rename(old_path, new_path)
        print(f"Renamed {old_path} to {new_path}")
