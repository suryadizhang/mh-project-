---
applyTo: '**'
---

# My Hibachi – Media Optimization Standards

**Priority: REFERENCE** – Use when adding images or videos to the
apps.

---

## 🎯 Purpose

All media files (images, videos) must be optimized for web before
deployment. Large media files are the #1 cause of poor Lighthouse
scores.

---

## 📹 Video Optimization (FFmpeg)

### When to Use:

- Adding new hero/background videos
- Any video > 2 MB
- Videos showing in above-the-fold content

### FFmpeg Commands:

#### Convert Video for Web (720p, ~1 Mbps):

```bash
ffmpeg -i input.mp4 \
  -vf "scale=1280:720" \
  -c:v libx264 \
  -preset slow \
  -crf 28 \
  -an \
  -movflags +faststart \
  output_optimized.mp4
```

**Options explained:**

| Option                 | Purpose                              |
| ---------------------- | ------------------------------------ |
| `-vf "scale=1280:720"` | Resize to 720p                       |
| `-c:v libx264`         | Use H.264 codec (universal support)  |
| `-preset slow`         | Better compression (slower encode)   |
| `-crf 28`              | Quality (18=high, 28=medium, 35=low) |
| `-an`                  | Remove audio (for decorative videos) |
| `-movflags +faststart` | Enable progressive loading           |

#### Extract Poster Frame from Video:

```bash
ffmpeg -i input.mp4 -vframes 1 -q:v 2 poster.jpg
```

#### Convert to WebM (smaller, modern browsers):

```bash
ffmpeg -i input.mp4 \
  -vf "scale=1280:720" \
  -c:v libvpx-vp9 \
  -crf 30 \
  -b:v 0 \
  -an \
  output.webm
```

---

## 🖼️ Image Optimization

### Target Sizes:

| Image Type     | Max Width | Max File Size | Format    |
| -------------- | --------- | ------------- | --------- |
| Hero/Banner    | 1920px    | 200 KB        | WebP/AVIF |
| Content images | 800px     | 100 KB        | WebP      |
| Thumbnails     | 400px     | 50 KB         | WebP      |
| Icons/logos    | As needed | 20 KB         | SVG/WebP  |

### Using `next/image` (Preferred):

```tsx
import Image from 'next/image';

// For LCP images (above the fold)
<Image
  src="/images/hero.jpg"
  alt="Description"
  width={1920}
  height={1080}
  priority  // Preloads the image
  quality={75}
  sizes="100vw"
/>

// For below-the-fold images
<Image
  src="/images/content.jpg"
  alt="Description"
  width={800}
  height={600}
  loading="lazy"  // Default behavior
  quality={75}
/>
```

### Manual Image Optimization (FFmpeg):

```bash
# Convert to WebP
ffmpeg -i input.jpg -quality 80 output.webp

# Resize and convert
ffmpeg -i input.jpg -vf "scale=800:-1" -quality 80 output.webp
```

---

## 📊 Media Audit Checklist

Before committing media files:

- [ ] Video < 2 MB (or lazy loaded)
- [ ] Images < 200 KB for hero, < 100 KB for content
- [ ] All videos have poster frames
- [ ] LCP images use `priority` prop
- [ ] Decorative videos have no audio track
- [ ] Videos use `+faststart` for progressive loading

---

## 🔧 Installing FFmpeg

### Windows (winget):

```powershell
winget install Gyan.FFmpeg
# Restart terminal after install
```

### macOS (Homebrew):

```bash
brew install ffmpeg
```

### Linux (apt):

```bash
sudo apt install ffmpeg
```

---

## 📁 Media File Locations

```
apps/customer/public/
├── images/
│   ├── hero-poster.jpg    # Hero video poster frame
│   ├── background.jpg     # Background images
│   └── blog/              # Blog post images
└── videos/
    ├── hero_video.mp4     # Hero background video
    └── *.vtt              # Video captions
```

---

## 🎯 Performance Targets

| Metric            | Target   | Critical Threshold |
| ----------------- | -------- | ------------------ |
| Total page weight | < 3 MB   | < 5 MB             |
| LCP image size    | < 100 KB | < 200 KB           |
| Video size        | < 2 MB   | < 5 MB             |
| Image load time   | < 1s     | < 2s               |

---

## 📝 Real Example: Hero Video Optimization

**Before optimization:**

- hero_video.mp4: 15.79 MB
- 1920x1080, 14.6 Mbps bitrate
- Mobile LCP: 10.6s ❌

**After optimization:**

- hero_video.mp4: 1.21 MB (92% smaller!)
- 1280x720, 1.1 Mbps bitrate
- Mobile LCP: ~2-3s ✅

**Command used:**

```bash
ffmpeg -i hero_video.mp4 \
  -vf "scale=1280:720" \
  -c:v libx264 \
  -preset slow \
  -crf 28 \
  -an \
  -movflags +faststart \
  hero_video_optimized.mp4
```

---

## 🔗 Related Docs

- `11-REACT_PERFORMANCE.instructions.md` – React optimization
- `apps/customer/src/lib/performance/` – Performance utilities
- Next.js Image Optimization:
  https://nextjs.org/docs/app/building-your-application/optimizing/images
