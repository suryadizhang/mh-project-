import Image from 'next/image'

interface BlogCardImageProps {
  post: {
    image?: string
    imageAlt?: string
    serviceArea: string
    eventType: string
    title: string
  }
  className?: string
}

export default function BlogCardImage({ post, className = "h-48" }: BlogCardImageProps) {
  if (post.image) {
    return (
      <div className={`${className} relative overflow-hidden`}>
        <Image
          src={post.image}
          alt={post.imageAlt || `${post.title} - ${post.serviceArea} ${post.eventType} hibachi catering`}
          width={400}
          height={300}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
        <div className="absolute bottom-4 left-4 right-4">
          <div className="text-white text-center">
            <div className="text-sm font-medium bg-black bg-opacity-50 rounded-lg px-3 py-1.5 backdrop-blur-sm">
              📍 {post.serviceArea} • 🎉 {post.eventType}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Fallback gradient for posts without images
  return (
    <div className={`${className} bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center relative`}>
      <div className="text-white text-center p-4">
        <div className="text-sm font-medium bg-black bg-opacity-30 rounded px-2 py-1">
          📍 {post.serviceArea} • 🎉 {post.eventType}
        </div>
      </div>
    </div>
  )
}
