# PWA Configuration Guide

The Meal Planner app is now configured as a Progressive Web App (PWA). This enables users to install the app on their devices and use it offline.

## Features Enabled

✅ **Install Prompt**: Users can install the app to their home screen  
✅ **Offline Support**: Service worker caches assets for offline use  
✅ **App Manifest**: Defines app name, icons, colors, and display mode  
✅ **Auto Updates**: Service worker automatically updates when new version deployed  
✅ **Asset Caching**: Images, CSS, and JS files cached for fast loading  
✅ **API Caching**: Network-first strategy for API calls with fallback cache  

## Configuration Files

### 1. vite.config.js
- Configured with `vite-plugin-pwa`
- Manifest settings for app metadata
- Workbox configuration for caching strategies
- Development mode enabled for testing

### 2. index.html
- Meta tags for mobile web app
- Theme color for status bar
- Apple-specific meta tags
- Icon references

### 3. Icons
Located in `frontend/public/`:
- `pwa-512x512.svg` - Main app icon (large)
- `pwa-192x192.svg` - Main app icon (small)
- `apple-touch-icon.svg` - iOS home screen icon
- `mask-icon.svg` - Safari pinned tab icon

## Testing PWA Locally

### 1. Build the app:
```bash
cd frontend
npm run build
```

### 2. Preview the production build:
```bash
npm run preview
```

### 3. Test in browser:
- Open Chrome/Edge DevTools (F12)
- Go to "Application" tab
- Check "Manifest" section
- Check "Service Workers" section
- Use "Lighthouse" tab to run PWA audit

## Installing the App

### Desktop (Chrome/Edge):
1. Visit the app URL
2. Look for install icon in address bar
3. Click "Install" button
4. App opens in standalone window

### Mobile (iOS Safari):
1. Visit the app URL
2. Tap Share button
3. Tap "Add to Home Screen"
4. Confirm installation

### Mobile (Android Chrome):
1. Visit the app URL
2. Tap menu (⋮)
3. Tap "Install app" or "Add to Home Screen"
4. Confirm installation

## Caching Strategies

### Static Assets (CacheFirst)
- Images (png, jpg, jpeg, svg, gif, webp)
- Cached for 30 days
- Max 100 entries

### API Calls (NetworkFirst)
- Attempts network request first
- Falls back to cache if offline
- Cached for 24 hours
- Max 50 entries

## Production Checklist

Before deploying to production:

- [ ] Replace SVG icons with PNG versions (required for most browsers)
- [ ] Generate icons using https://realfavicongenerator.net/
- [ ] Update theme colors to match brand
- [ ] Test install flow on iOS Safari
- [ ] Test install flow on Android Chrome
- [ ] Test install flow on desktop Chrome/Edge
- [ ] Run Lighthouse PWA audit (target score: 90+)
- [ ] Test offline functionality
- [ ] Verify service worker registration
- [ ] Check manifest.json in browser DevTools

## Generating Production Icons

### Option 1: Online Generator (Recommended)
1. Visit https://realfavicongenerator.net/
2. Upload your logo/icon (at least 512x512 PNG)
3. Configure settings for each platform
4. Download generated package
5. Replace files in `frontend/public/`

### Option 2: ImageMagick (Command Line)
```bash
cd frontend/public
# Create base icon first (512x512 PNG)
convert your-logo.png -resize 512x512 pwa-512x512.png
convert your-logo.png -resize 192x192 pwa-192x192.png
convert your-logo.png -resize 180x180 apple-touch-icon.png
convert your-logo.png -resize 32x32 favicon.ico
```

### Option 3: PWA Builder
1. Visit https://www.pwabuilder.com/imageGenerator
2. Upload your icon
3. Download generated package
4. Replace files in `frontend/public/`

## Icon Requirements

| File | Size | Format | Purpose |
|------|------|--------|---------|
| pwa-512x512.png | 512×512 | PNG | Android Chrome, Windows |
| pwa-192x192.png | 192×192 | PNG | Android Chrome (small) |
| apple-touch-icon.png | 180×180 | PNG | iOS home screen |
| favicon.ico | 32×32 | ICO | Browser tab icon |
| mask-icon.svg | Any | SVG | Safari pinned tabs |

### Icon Design Tips:
- Use simple, recognizable imagery
- Ensure legibility at 192×192 (smallest required size)
- Avoid text unless it's part of your logo
- Use consistent brand colors
- Test on both light and dark backgrounds
- Consider safe zones for maskable icons (80% of image area)

## Troubleshooting

### Service Worker Not Registering
- Check browser console for errors
- Ensure HTTPS is enabled (required for PWA)
- Clear browser cache and reload
- Check that `dist/sw.js` exists after build

### Install Prompt Not Showing
- PWA criteria must be met (manifest, service worker, HTTPS)
- User must engage with site before prompt
- May be blocked if previously dismissed
- Check DevTools > Application > Manifest

### Icons Not Displaying
- Ensure PNG format (not SVG) for production
- Check file paths in manifest
- Verify files exist in `public/` directory
- Clear cache and rebuild

### Offline Mode Not Working
- Check service worker is active
- Verify cache strategies in vite.config.js
- Test with DevTools offline mode
- Check network tab for cached resources

## Updates and Versioning

The service worker will automatically update when you deploy a new version:

1. User visits site with old version
2. Service worker detects new version in background
3. New version downloaded and cached
4. User prompted to reload (automatic in most cases)
5. New version active after reload

## Monitoring

Monitor PWA metrics:
- Install rate
- Offline usage
- Service worker errors
- Cache hit rates
- Update success rates

Use tools like:
- Google Analytics (with offline tracking)
- Sentry (for error monitoring)
- Lighthouse CI (for automated audits)

## Additional Resources

- [PWA Builder](https://www.pwabuilder.com/)
- [Workbox Documentation](https://developers.google.com/web/tools/workbox)
- [Vite PWA Plugin](https://vite-pwa-org.netlify.app/)
- [MDN PWA Guide](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [Web.dev PWA](https://web.dev/progressive-web-apps/)
