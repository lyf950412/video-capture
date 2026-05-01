from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        padding = size // 16
        r = size - padding * 2
        
        draw.rounded_rectangle(
            [padding, padding, size - padding, size - padding],
            radius=size // 6,
            fill=(239, 68, 68, 255)
        )
        
        cx, cy = size / 2, size / 2
        icon_size = size // 3
        
        draw.polygon([
            (cx - icon_size // 2, cy - icon_size),
            (cx - icon_size // 2, cy + icon_size),
            (cx + icon_size, cy)
        ], fill=(255, 255, 255, 255))
        
        images.append(img)
    
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icon.ico')
    os.makedirs(os.path.dirname(icon_path), exist_ok=True)
    images[0].save(icon_path, format='ICO', sizes=[(s, s) for s in sizes])
    print(f"Icon saved to: {icon_path}")

if __name__ == '__main__':
    create_icon()
