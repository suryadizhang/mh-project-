// Simple vector search implementation for local data
// Uses cosine similarity for text matching

import { DEFAULT_PRICING, interpolatePricing, type PricingValues } from './pricingTemplates';

interface SearchResult {
  content: string;
  title: string;
  href: string;
  score: number;
  category: string;
}

interface DataEntry {
  question?: string;
  answer?: string;
  title?: string;
  description?: string;
  content?: string;
  category: string;
  href: string;
  keywords?: string[];
}

// Simple text preprocessing
function preprocessText(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .split(/\s+/)
    .filter((word) => word.length > 2)
    .filter(
      (word) =>
        !['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'].includes(
          word,
        ),
    );
}

// Calculate term frequency
function getTermFrequency(terms: string[]): Map<string, number> {
  const freq = new Map<string, number>();
  terms.forEach((term) => {
    freq.set(term, (freq.get(term) || 0) + 1);
  });
  return freq;
}

// Calculate TF-IDF score
function calculateTFIDF(
  queryTerms: string[],
  documentTerms: string[],
  allDocuments: string[][],
): number {
  const queryTF = getTermFrequency(queryTerms);
  const docTF = getTermFrequency(documentTerms);
  const docCount = allDocuments.length;

  let score = 0;

  for (const [term, qFreq] of queryTF.entries()) {
    const docFreq = docTF.get(term) || 0;
    if (docFreq > 0) {
      // Calculate IDF
      const docsWithTerm = allDocuments.filter((doc) => doc.includes(term)).length;
      const idf = Math.log(docCount / (docsWithTerm + 1));

      // TF-IDF score
      score += qFreq * docFreq * idf;
    }
  }

  // Normalize by document length
  const docLength = Math.sqrt(documentTerms.length);
  const queryLength = Math.sqrt(queryTerms.length);

  return score / (docLength * queryLength + 1);
}

// Load data based on page context
// Interpolates pricing placeholders with values from pricing config
async function loadData(
  page: string,
  pricing: PricingValues = DEFAULT_PRICING,
): Promise<DataEntry[]> {
  try {
    const dataFiles: DataEntry[] = [];

    // Always include FAQ data
    const faqModule = await import('@/data/faq.json');
    const faqData = (faqModule.default as DataEntry[]).map((item) => ({
      ...item,
      answer: item.answer ? interpolatePricing(item.answer, pricing) : undefined,
      content: item.content ? interpolatePricing(item.content, pricing) : undefined,
    }));
    dataFiles.push(...faqData);

    // Add page-specific data
    if (page === '/menu') {
      const menuModule = await import('@/data/menu.json');
      dataFiles.push(...(menuModule.default as DataEntry[]));
    }

    // Always include policies for all pages
    const policiesModule = await import('@/data/policies.json');
    const policiesData = (policiesModule.default as DataEntry[]).map((item) => ({
      ...item,
      answer: item.answer ? interpolatePricing(item.answer, pricing) : undefined,
      content: item.content ? interpolatePricing(item.content, pricing) : undefined,
    }));
    dataFiles.push(...policiesData);

    return dataFiles;
  } catch (error) {
    console.error('Error loading data:', error);
    // Return fallback data
    return [
      {
        title: 'Contact Support',
        content:
          'For specific questions about our hibachi catering service, please contact us directly.',
        category: 'general',
        href: '/contact',
      },
    ];
  }
}

export async function cosineSearch(query: string, page: string): Promise<SearchResult[]> {
  try {
    const data = await loadData(page);
    const queryTerms = preprocessText(query);

    if (queryTerms.length === 0) {
      return [];
    }

    // Prepare all documents for IDF calculation
    const allDocuments = data.map((item) => {
      const searchableText = [
        item.question || '',
        item.answer || '',
        item.title || '',
        item.description || '',
        item.content || '',
        ...(item.keywords || []),
      ].join(' ');

      return preprocessText(searchableText);
    });

    // Calculate scores for each data entry
    const results: SearchResult[] = data.map((item) => {
      const searchableText = [
        item.question || '',
        item.answer || '',
        item.title || '',
        item.description || '',
        item.content || '',
        ...(item.keywords || []),
      ].join(' ');

      const documentTerms = preprocessText(searchableText);
      const score = calculateTFIDF(queryTerms, documentTerms, allDocuments);

      return {
        content: item.answer || item.content || item.description || '',
        title: item.question || item.title || 'Information',
        href: item.href,
        score,
        category: item.category,
      };
    });

    // Sort by score and return top results
    return results
      .filter((result) => result.score > 0.1) // Minimum threshold
      .sort((a, b) => b.score - a.score)
      .slice(0, 5); // Top 5 results
  } catch (error) {
    console.error('Vector search error:', error);
    return [];
  }
}
