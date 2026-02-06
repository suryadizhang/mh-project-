export default function QuoteLayout({ children }: { children: React.ReactNode }) {
  return (
    <div data-page="quote" className="w-full">
      {children}
    </div>
  );
}
