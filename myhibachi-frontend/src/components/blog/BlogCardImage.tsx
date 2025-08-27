import LazyBlogImage from './LazyBlogImage'

interface BlogCardImageProps {
  post: {
    image?: string
    imageAlt?: string
    serviceArea: string
    eventType: string
    title: string
  }
  className?: string
  priority?: boolean
}

export default function BlogCardImage({ post, className = "h-48", priority = false }: BlogCardImageProps) {
  if (post.image) {
    return (
      <div className={`${className} relative overflow-hidden group`}>
        <LazyBlogImage
          src={post.image}
          alt={post.imageAlt || `${post.title} - ${post.serviceArea} ${post.eventType} hibachi catering`}
          width={400}
          height={300}
          className="w-full h-full"
          priority={priority}
          fallbackSrc="/images/blog/hibachi-chef-cooking.svg"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
        <div className="absolute bottom-4 left-4 right-4">
          <div className="text-white text-center">
            <div className="text-sm font-medium bg-black bg-opacity-50 rounded-lg px-3 py-1.5 backdrop-blur-sm border border-white/20">
              📍 {post.serviceArea} • 🎉 {post.eventType}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Fallback gradient for posts without images
  return (
    <div className={`${className} bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center relative group`}>
      <div className="text-white text-center p-4">
        <div className="text-sm font-medium bg-black bg-opacity-30 rounded px-2 py-1 transition-all duration-300 group-hover:bg-opacity-50">
          📍 {post.serviceArea} • 🎉 {post.eventType}
        </div>
      </div>
      {/* Enhanced gradient overlay for fallback */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    </div>
  )
}
