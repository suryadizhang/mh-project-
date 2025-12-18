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

## �️ Available Tools

We have two CLI tools available for media optimization:

| Tool            | Best For                        | Installed |
| --------------- | ------------------------------- | --------- |
| **FFmpeg**      | Video transcoding, format conv. | ✅        |
| **ImageMagick** | Image optimization, WebP/AVIF   | ✅ v7.1.2 |

---

## 🖼️ Image Optimization (ImageMagick) - PREFERRED

ImageMagick is our primary tool for image optimization. It's faster
and more specialized for images than FFmpeg.

### Quick Reference Commands:

```powershell
# Convert to WebP (52% smaller than JPEG typically)
magick input.jpg -quality 80 output.webp

# Convert to AVIF (even smaller, modern browsers)
magick input.jpg -quality 50 output.avif

# Resize and convert (maintain aspect ratio)
magick input.jpg -resize 1920x1080 -quality 80 output.webp

# Resize to specific width (height auto-calculated)
magick input.jpg -resize 800x -quality 80 output.webp

# Batch convert all JPGs in folder to WebP
Get-ChildItem *.jpg | ForEach-Object { magick $_.Name -quality 80 ($_.BaseName + ".webp") }
```

### Recommended Quality Settings:

| Format | Quality | Use Case                      |
| ------ | ------- | ----------------------------- |
| WebP   | 75-85   | General use, good balance     |
| WebP   | 60-70   | Thumbnails, non-critical      |
| AVIF   | 50-60   | Modern browsers, best savings |
| JPEG   | 80-85   | Fallback only                 |

### Hero/LCP Image Optimization:

```powershell
# Optimize hero image for LCP (critical path)
cd apps/customer/public/images

# Create WebP version (primary)
magick hero-poster.jpg -quality 80 hero-poster.webp

# Create AVIF version (best compression, optional)
magick hero-poster.jpg -quality 50 hero-poster.avif

# Verify sizes
Get-ChildItem hero-poster.* | Select-Object Name, @{N='SizeKB';E={[math]::Round($_.Length/1KB,1)}}
```

### Creating Responsive Images:

```powershell
# Create multiple sizes for srcset
magick input.jpg -resize 480x -quality 80 image-480w.webp
magick input.jpg -resize 768x -quality 80 image-768w.webp
magick input.jpg -resize 1200x -quality 80 image-1200w.webp
magick input.jpg -resize 1920x -quality 80 image-1920w.webp
```

### Image Info and Analysis:

```powershell
# Get image dimensions and format
magick identify input.jpg

# Get detailed info
magick identify -verbose input.jpg | Select-String -Pattern "Geometry|Filesize|Format"
```

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
# Then optimize with ImageMagick
magick poster.jpg -quality 80 poster.webp
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

## 🎯 Target Sizes and Formats

| Image Type     | Max Width | Max File Size | Format          |
| -------------- | --------- | ------------- | --------------- |
| Hero/Banner    | 1920px    | 100 KB        | WebP + fallback |
| Content images | 800px     | 80 KB         | WebP            |
| Thumbnails     | 400px     | 30 KB         | WebP            |
| Icons/logos    | As needed | 20 KB         | SVG preferred   |

---

## 🔧 Using in Next.js Components

### For LCP Images (Hero) - Use Native `<picture>`:

```tsx
// Server component for instant LCP - NO JavaScript dependency
export function HeroImage() {
  return (
    <picture>
      <source srcSet="/images/hero.webp" type="image/webp" />
      <source srcSet="/images/hero.avif" type="image/avif" />
      <img
        src="/images/hero.jpg"
        alt="Hero"
        width={1920}
        height={1080}
        decoding="sync"
        fetchPriority="high"
      />
    </picture>
  );
}
```

### For Non-LCP Images - Use `next/image`:

```tsx
import Image from 'next/image';

// Below-the-fold, let Next.js handle optimization
<Image
  src="/images/content.jpg"
  alt="Description"
  width={800}
  height={600}
  loading="lazy"
  quality={75}
/>;
```

---

## 📊 Media Audit Checklist

Before committing media files:

- [ ] Images converted to WebP (use ImageMagick)
- [ ] Images < 100 KB for hero, < 80 KB for content
- [ ] Video < 2 MB (or lazy loaded)
- [ ] All videos have WebP poster frames
- [ ] LCP images use native `<picture>` with `fetchPriority="high"`
- [ ] Decorative videos have no audio track
- [ ] Videos use `+faststart` for progressive loading

---

## 🔧 Installing Tools

### ImageMagick (Windows):

```powershell
winget install ImageMagick.ImageMagick
# Restart terminal after install
# Verify: magick --version
```

### FFmpeg (Windows):

```powershell
winget install Gyan.FFmpeg
# Restart terminal after install
# Verify: ffmpeg -version
```

### macOS (Homebrew):

```bash
brew install imagemagick ffmpeg
```

### Linux (apt):

```bash
sudo apt install imagemagick ffmpeg
```

---

## 📁 Media File Locations

```
apps/customer/public/
├── images/
│   ├── hero-poster.webp   # Hero image (WebP primary)
│   ├── hero-poster.jpg    # Hero image (JPEG fallback)
│   ├── background.webp    # Background images
│   └── blog/              # Blog post images
└── videos/
    ├── hero_video.mp4     # Hero background video
    └── *.vtt              # Video captions
```

---

## 🎯 Performance Targets

| Metric            | Target  | Critical Threshold |
| ----------------- | ------- | ------------------ |
| Total page weight | < 3 MB  | < 5 MB             |
| LCP image size    | < 50 KB | < 100 KB           |
| Video size        | < 2 MB  | < 5 MB             |
| Image load time   | < 500ms | < 1s               |

---

## 📝 Real Examples

### Hero Image Optimization:

**Before:**

- hero-poster.jpg: 91 KB

**After:**

- hero-poster.webp: 43 KB (52% smaller!)

**Command:**

```powershell
magick hero-poster.jpg -quality 80 hero-poster.webp
```

### Hero Video Optimization:

**Before:**

- hero_video.mp4: 15.79 MB
- 1920x1080, 14.6 Mbps bitrate

**After:**

- hero_video.mp4: 1.21 MB (92% smaller!)
- 1280x720, 1.1 Mbps bitrate

**Command:**

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
- ImageMagick Docs:
  https://imagemagick.org/script/command-line-processing.php
