# 📸 Image Upload Setup Guide

## Quick Decision: Where to Store Images?

### ✅ **RECOMMENDED: Cloudinary (FREE)**

**Why Cloudinary?**

- ✅ **FREE:** 25GB storage + 25GB bandwidth/month
- ✅ **Zero cost** until you hit 1000+ reviews/month
- ✅ **Auto-optimization:** Compresses, resizes, converts to WebP
- ✅ **CDN included:** Fast delivery worldwide
- ✅ **No Vercel issues:** Works perfectly with serverless
- ✅ **5-minute setup**

**Cloudinary handles:**

- Image resizing (1920x1920 max)
- Thumbnail generation (400x300)
- Format conversion (WebP for modern browsers)
- Compression (quality: auto)
- Global CDN delivery

---

## Setup Instructions

### Option 1: Cloudinary (Recommended) - 5 Minutes

#### Step 1: Sign Up (Free)

```bash
1. Go to: https://cloudinary.com/users/register/free
2. Sign up with email
3. Confirm email
4. Go to Dashboard
```

#### Step 2: Get Credentials

```bash
Dashboard → Settings → Account
Copy these 3 values:
- Cloud Name: your-cloud-name
- API Key: 123456789012345
- API Secret: aBcDeFgHiJkLmNoPqRsTuVwXyZ
```

#### Step 3: Add to Backend .env

```bash
# Open: apps/backend/.env
# Add these lines:

CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=aBcDeFgHiJkLmNoPqRsTuVwXyZ
```

#### Step 4: Install Python Package

```bash
cd apps/backend
pip install cloudinary pillow python-multipart
```

#### Step 5: Test Upload (Optional)

```python
# Test in Python console
import cloudinary
cloudinary.config(
    cloud_name="your-cloud-name",
    api_key="your-api-key",
    api_secret="your-api-secret"
)

# Upload test image
result = cloudinary.uploader.upload("test.jpg")
print(result['secure_url'])  # Should print image URL
```

**Done!** ✅ Images now upload to Cloudinary with auto-optimization

---

### Option 2: Local Filesystem (Development Only)

**Use this if:** You don't want to set up Cloudinary yet (testing
only)

**Limitations:**

- ❌ Won't work on Vercel (serverless, no persistent storage)
- ❌ No CDN (slower)
- ❌ Manual optimization required
- ❌ Not suitable for production

**Setup:**

1. Images saved to: `apps/customer/public/uploads/reviews/`
2. Accessed via: `http://localhost:3000/uploads/reviews/image.jpg`
3. No configuration needed - works automatically

**When you deploy to Vercel, you MUST switch to Cloudinary or S3**

---

## How Images Are Displayed

### 1. Customer Review Newsfeed (`/reviews`)

```typescript
// Customer sees approved reviews with images
<div className="image-gallery grid grid-cols-3 gap-1">
  {review.images.slice(0, 6).map((image, i) => (
    <Image
      src={image.thumbnail}  // Fast-loading thumbnail
      onClick={() => openLightbox(image.url)}  // Click for full size
    />
  ))}
</div>
```

**Features:**

- ✅ Image gallery (1-6 images per review)
- ✅ Click to open lightbox (fullscreen)
- ✅ Lazy loading (only loads when scrolling)
- ✅ Mobile responsive
- ✅ "+X more" indicator if >6 images

### 2. Admin Moderation Panel

```typescript
// Admin sees images before approval
<div className="review-preview">
  <h3>{review.title}</h3>
  <p>{review.content}</p>

  {/* Image preview */}
  <div className="images grid grid-cols-4">
    {review.images.map(img => (
      <Image src={img.thumbnail} />
    ))}
  </div>

  <button onClick={() => approve(review.id)}>Approve</button>
  <button onClick={() => reject(review.id)}>Reject</button>
</div>
```

**Admin can:**

- ✅ Preview all images before approval
- ✅ See customer details
- ✅ Approve/reject reviews
- ✅ Bulk actions

### 3. Review Submission Form

```typescript
// Customer uploads images
<input
  type="file"
  accept="image/*"
  multiple
  onChange={handleImageUpload}
/>

{/* Preview before submit */}
<div className="preview-grid">
  {previews.map((preview, i) => (
    <div className="relative">
      <Image src={preview} />
      <button onClick={() => removeImage(i)}>✕</button>
    </div>
  ))}
</div>
```

**Customer can:**

- ✅ Upload up to 10 images
- ✅ Preview before submitting
- ✅ Remove images
- ✅ Drag & drop (optional enhancement)

---

## Cost Comparison

| Storage           | Free Tier                      | Cost After Free | Best For       |
| ----------------- | ------------------------------ | --------------- | -------------- |
| **Cloudinary**    | 25GB storage<br>25GB bandwidth | $89/month (Pro) | **Production** |
| **AWS S3**        | 5GB for 12 months              | ~$0.50/month    | Production     |
| **Cloudflare R2** | 10GB storage                   | $0.015/GB       | Production     |
| **Local**         | Unlimited                      | Can't deploy    | Dev only       |

**For your scale (100-500 reviews/month):**

- Cloudinary FREE tier = **Perfect fit** ✅
- You'll stay in free tier for ~12+ months
- 25GB = ~5,000 high-quality images

---

## Image Storage Flow

### Upload Process:

```
Customer submits review with images
         ↓
FastAPI receives files
         ↓
ImageService.upload_review_images()
         ↓
Upload to Cloudinary (auto-optimize)
         ↓
Get URLs (main + thumbnail)
         ↓
Save URLs to database (customer_review_blog_posts.images)
         ↓
Admin reviews (sees thumbnails)
         ↓
Admin approves
         ↓
Images appear on /reviews page
         ↓
Customers see gallery with lightbox
```

### Database Storage:

```json
// customer_review_blog_posts.images (JSON column)
[
  {
    "url": "https://res.cloudinary.com/your-cloud/image/upload/v1/reviews/abc123.jpg",
    "thumbnail": "https://res.cloudinary.com/your-cloud/image/upload/c_fill,h_300,w_400/reviews/abc123.jpg",
    "width": 1920,
    "height": 1080,
    "format": "jpg",
    "size": 245678,
    "filename": "customer_photo.jpg"
  }
  // ... more images
]
```

---

## Summary

**For Production:**

1. ✅ Use **Cloudinary FREE tier**
2. ✅ 5-minute setup (sign up → get credentials → add to .env)
3. ✅ Images automatically optimized
4. ✅ Global CDN delivery
5. ✅ $0 cost for first 25GB

**For Development:**

1. ⚠️ Can use **local filesystem** (testing only)
2. ⚠️ Must switch to Cloudinary before Vercel deploy

**Images Display On:**

- ✅ Customer review newsfeed (`/reviews`)
- ✅ Individual review pages (`/reviews/[id]`)
- ✅ Admin moderation panel (preview before approval)
- ✅ Mobile & desktop (fully responsive)

---

## Next Steps

1. **Sign up for Cloudinary** (5 min):
   https://cloudinary.com/users/register/free
2. **Add credentials to .env** (1 min)
3. **Install packages:**
   `pip install cloudinary pillow python-multipart`
4. **Test upload** (optional)
5. **Deploy!** ✅

That's it! Images will work perfectly on Vercel with Cloudinary. 🚀
