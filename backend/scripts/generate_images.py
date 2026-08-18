import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_image(filename, text, blurry=False):
    os.makedirs('images', exist_ok=True)
    img = Image.new('RGB', (400, 300), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # Draw some text
    draw.text((50, 100), "BANK TRANSFER RECEIPT", fill=(50, 50, 50))
    draw.text((50, 140), text, fill=(0, 0, 0))
    
    if blurry:
        img = img.filter(ImageFilter.GaussianBlur(radius=5))
        
    img.save(f'images/{filename}')
    print(f'Generated {filename}')

create_image('slip1.jpg', 'Amount: Rs. 25000.00\nA/C: 100200300\nRef: 839201')
create_image('slip2.jpg', 'Amount: Rs. 10000.00\nA/C: 100200300\nRef: 111111')
create_image('slip1_copy.jpg', 'Amount: Rs. 25000.00\nA/C: 100200300\nRef: 839201')
create_image('blurry.jpg', 'Amount: Rs. 5000.00\nA/C: 100200300\nRef: 999999', blurry=True)
