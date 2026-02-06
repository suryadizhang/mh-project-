import LazyBlogImage from './LazyBlogImage';

interface BlogCardImageProps {
  post: {
    image?: string;
    imageAlt?: string;
    serviceArea: string;
    eventType: string;
    title: string;
  };
  className?: string;
  priority?: boolean;
}

export default function BlogCardImage({
  post,
  className = 'h-48',
  priority = false,
}: BlogCardImageProps) {
  if (post.image) {
    return (
      <div className={`${className} group relative overflow-hidden`}>
        <LazyBlogImage
          src={post.image}
          alt={
            post.imageAlt ||
            `${post.title} - ${post.serviceArea} ${post.eventType} hibachi catering`
          }
          width={400}
          height={300}
          className="h-full w-full"
          priority={priority}
          fallbackSrc="/images/blog/hibachi-chef-cooking.svg"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
        <div className="absolute right-4 bottom-4 left-4">
          <div className="text-center text-white">
            <div className="bg-opacity-50 rounded-lg border border-white/20 bg-black px-3 py-1.5 text-sm font-medium backdrop-blur-sm">
              📍 {post.serviceArea} • 🎉 {post.eventType}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Fallback gradient for posts without images
  return (
    <div
      className={`${className} group relative flex items-center justify-center bg-gradient-to-br from-orange-500 to-red-600`}
    >
      <div className="p-4 text-center text-white">
        <div className="bg-opacity-30 group-hover:bg-opacity-50 rounded bg-black px-2 py-1 text-sm font-medium transition-all duration-300">
          📍 {post.serviceArea} • 🎉 {post.eventType}
        </div>
      </div>
      {/* Enhanced gradient overlay for fallback */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/10 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
    </div>
  );
}
