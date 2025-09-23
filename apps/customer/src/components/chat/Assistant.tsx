// Legacy Assistant component - now using ChatWidget via ClientLayout
// This file is kept for compatibility but functionality moved to ChatWidget

interface AssistantProps {
  page?: string
}

export default function Assistant({ page }: AssistantProps = {}) {
  // Component no longer renders anything - ChatWidget handles all chat functionality
  // The page prop is ignored as context is handled by the main ChatWidget
  console.log('Legacy Assistant component rendered for page:', page)
  return null
}
