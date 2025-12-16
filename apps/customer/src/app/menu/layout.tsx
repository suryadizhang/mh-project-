export default function MenuLayout({ children }: { children: React.ReactNode }) {
  return (
    <div data-page="menu" className="page-wrapper w-full">
      {children}
    </div>
  )
}
