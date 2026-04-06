<!-- Favicon Creation Instructions for Policy Helper AI -->

FAVICON SETUP GUIDE
===================

Your favicon files should be placed in the /static folder.

REQUIRED FILES:
1. favicon.ico - Main favicon (32x32 pixels, .ico format)
2. apple-touch-icon.png - For Apple devices (180x180 pixels, .png format)
3. og-image.png - For social media sharing (1200x630 pixels, .png format)

HOW TO CREATE A FAVICON:
========================

Option 1: Use Online Favicon Generator (RECOMMENDED - Takes 2 minutes)
--------
1. Go to https://favicon-generator.org/ or https://www.favicon-generator.com/
2. Upload your logo or create a simple design with your brand color (#c9a84c gold)
3. Download the favicon.ico file
4. Save to: /static/favicon.ico

Option 2: Use Python PIL (if you have it installed)
--------
from PIL import Image, ImageDraw

# Create a 32x32 favicon
img = Image.new('RGB', (32, 32), color=(201, 168, 76))  # Gold color
draw = ImageDraw.Draw(img)
draw.text((8, 8), 'P', fill=(26, 26, 26))  # Dark text for "Policy"
img.save('static/favicon.ico')

Option 3: Use Your Existing Logo
--------
1. Save your logo as a 32x32 pixel .ico file
2. Save as: /static/favicon.ico

APPLE TOUCH ICON:
=================
For best results on iPhones and iPads:
1. Create or find a 180x180 pixel PNG image
2. Should have rounded corners or be square
3. Save as: /static/apple-touch-icon.png

OPEN GRAPH IMAGE:
=================
For social media sharing:
1. Create a 1200x630 pixel PNG image
2. Should include your brand name and key message
3. Save as: /static/og-image.png

QUICK TEMPORARY SOLUTION:
=========================
If you don't have favicon files yet, use emoji converter:
1. Go to https://www.favicon-generator.com/
2. Type "P" in the text field
3. Use gold color background (#c9a84c)
4. Download and save to /static/favicon.ico

FILES CHECKLIST:
================
- [ ] favicon.ico (32x32)
- [ ] apple-touch-icon.png (180x180)
- [ ] og-image.png (1200x630)

All files should be in: a:\Project-2\static\

Once created, your landing.html already references them correctly in the <head> section.
