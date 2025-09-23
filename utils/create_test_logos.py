from PIL import Image, ImageDraw, ImageFont
import os

# Create logos directory if it doesn't exist
logos_dir = "data/logos"
os.makedirs(logos_dir, exist_ok=True)

# Create a simple test logo for tournament ID 1 (usually Australian Open)
def create_test_logo():
    # Create a 32x32 image with a blue background
    img = Image.new('RGBA', (32, 32), (52, 152, 219, 255))  # Blue background
    draw = ImageDraw.Draw(img)
    
    # Draw a simple tennis ball design
    # White circle
    draw.ellipse([4, 4, 28, 28], fill='white', outline='black', width=2)
    
    # Tennis ball curved lines
    draw.arc([4, 4, 28, 28], start=0, end=180, fill='black', width=2)
    draw.arc([4, 4, 28, 28], start=180, end=360, fill='black', width=2)
    
    # Save the logo
    img.save(f"{logos_dir}/1.png")
    print("Created test logo for tournament ID 1")

# Create a few more test logos
def create_more_test_logos():
    colors = [
        (142, 68, 173),  # Purple for Grand Slam
        (230, 126, 34),  # Orange for Masters
        (243, 156, 18),  # Gold for ATP 500
        (52, 152, 219),  # Blue for ATP 250
    ]
    
    for i, color in enumerate(colors, start=2):
        img = Image.new('RGBA', (32, 32), (*color, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw a simple design (circle with number)
        draw.ellipse([6, 6, 26, 26], fill='white', outline='black', width=2)
        
        # Draw tournament number/letter
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        text = str(i)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (32 - text_width) // 2
        y = (32 - text_height) // 2 - 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        img.save(f"{logos_dir}/{i}.png")
    
    print(f"Created test logos for tournament IDs 2-{len(colors)+1}")

if __name__ == "__main__":
    create_test_logo()
    create_more_test_logos()