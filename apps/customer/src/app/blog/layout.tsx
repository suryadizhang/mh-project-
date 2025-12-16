export default function BlogLayout({ children }: { children: React.ReactNode }) {
  return (
    <div data-page="blog" className="w-full" style={{ width: '100%', display: 'block' }}>
      {children}
    </div>
  )
}
