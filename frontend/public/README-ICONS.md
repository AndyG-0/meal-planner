# PWA Icons

This directory contains placeholder icons for the PWA. For production use, please replace these with professionally designed icons.

## Required Icon Files

Generate these from your icon design:

1. **pwa-192x192.png** - 192x192 PNG icon
2. **pwa-512x512.png** - 512x512 PNG icon  
3. **apple-touch-icon.png** - 180x180 PNG for iOS
4. **favicon.ico** - 32x32 or 16x16 ICO file

## Generating Icons

You can use the provided `pwa-icon.svg` as a starting point and convert it using:

### Using ImageMagick (if installed):
```bash
convert pwa-icon.svg -resize 512x512 pwa-512x512.png
convert pwa-icon.svg -resize 192x192 pwa-192x192.png
convert pwa-icon.svg -resize 180x180 apple-touch-icon.png
convert pwa-icon.svg -resize 32x32 favicon.ico
```

### Using online tools:
- https://realfavicongenerator.net/
- https://www.pwabuilder.com/imageGenerator

### Design Tips:
- Use simple, recognizable imagery
- Ensure icons work at small sizes (192x192)
- Consider maskable icons (icons with safe zone padding)
- Use brand colors consistently
- Test on both light and dark backgrounds
