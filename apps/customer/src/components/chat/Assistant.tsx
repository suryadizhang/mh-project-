// Legacy Assistant component - now using ChatWidget via ClientLayout
// This file is kept for compatibility but functionality moved to ChatWidget

import { logger } from '@/lib/logger';

interface AssistantProps {
  page?: string
}

export default function Assistant({ page }: AssistantProps = {}) {
  // Component no longer renders anything - ChatWidget handles all chat functionality
  // The page prop is ignored as context is handled by the main ChatWidget
  logger.debug('Legacy Assistant component rendered', { page })
  return null
}
