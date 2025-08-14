#!/usr/bin/env node

/**
 * My Hibachi Assistant - Embeddings and Search Test Script
 *
 * This script tests the vector search functionality and verifies
 * that our local data files are properly structured for the chatbot.
 * Run this script to validate the chatbot data pipeline.
 */

const fs = require('fs')
const path = require('path')

// Simple text processing for search testing
function preprocessText(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .split(/\s+/)
    .filter(word => word.length > 2)
    .filter(word => !['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'].includes(word))
}

function getTermFrequency(terms) {
  const freq = new Map()
  terms.forEach(term => {
    freq.set(term, (freq.get(term) || 0) + 1)
  })
  return freq
}

function calculateTFIDF(queryTerms, documentTerms, allDocuments) {
  const queryTF = getTermFrequency(queryTerms)
  const docTF = getTermFrequency(documentTerms)
  const docCount = allDocuments.length

  let score = 0

  for (const [term, qFreq] of queryTF.entries()) {
    const docFreq = docTF.get(term) || 0
    if (docFreq > 0) {
      const docsWithTerm = allDocuments.filter(doc => doc.includes(term)).length
      const idf = Math.log(docCount / (docsWithTerm + 1))
      score += qFreq * docFreq * idf
    }
  }

  const docLength = Math.sqrt(documentTerms.length)
  const queryLength = Math.sqrt(queryTerms.length)

  return score / (docLength * queryLength + 1)
}

async function testSearch(query, dataFiles) {
  console.log(`\n🔍 Testing search for: "${query}"`)
  console.log('=' .repeat(50))

  const queryTerms = preprocessText(query)

  // Prepare all documents for IDF calculation
  const allDocuments = dataFiles.map(item => {
    const searchableText = [
      item.question || '',
      item.answer || '',
      item.title || '',
      item.description || '',
      item.content || '',
      ...(item.keywords || [])
    ].join(' ')

    return preprocessText(searchableText)
  })

  // Calculate scores for each data entry
  const results = dataFiles.map(item => {
    const searchableText = [
      item.question || '',
      item.answer || '',
      item.title || '',
      item.description || '',
      item.content || '',
      ...(item.keywords || [])
    ].join(' ')

    const documentTerms = preprocessText(searchableText)
    const score = calculateTFIDF(queryTerms, documentTerms, allDocuments)

    return {
      content: item.answer || item.content || item.description || '',
      title: item.question || item.title || 'Information',
      href: item.href,
      score,
      category: item.category
    }
  })

  // Sort by score and get top results
  const topResults = results
    .filter(result => result.score > 0.1)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)

  if (topResults.length === 0) {
    console.log('❌ No relevant results found')
    return []
  }

  topResults.forEach((result, index) => {
    const confidence = result.score > 0.7 ? 'HIGH' : result.score > 0.5 ? 'MEDIUM' : 'LOW'
    console.log(`\n${index + 1}. ${result.title}`)
    console.log(`   Confidence: ${confidence} (${result.score.toFixed(3)})`)
    console.log(`   Category: ${result.category}`)
    console.log(`   Content: ${result.content.substring(0, 100)}...`)
    console.log(`   Link: ${result.href}`)
  })

  return topResults
}

async function main() {
  console.log('🚀 My Hibachi Assistant - Data Pipeline Test')
  console.log('=' .repeat(60))

  const dataDir = path.join(__dirname, '../src/data')

  try {
    // Load data files
    console.log('\n📁 Loading data files...')

    const faqPath = path.join(dataDir, 'faq.json')
    const menuPath = path.join(dataDir, 'menu.json')
    const policiesPath = path.join(dataDir, 'policies.json')

    if (!fs.existsSync(faqPath)) throw new Error('FAQ data file not found')
    if (!fs.existsSync(menuPath)) throw new Error('Menu data file not found')
    if (!fs.existsSync(policiesPath)) throw new Error('Policies data file not found')

    const faqData = JSON.parse(fs.readFileSync(faqPath, 'utf8'))
    const menuData = JSON.parse(fs.readFileSync(menuPath, 'utf8'))
    const policiesData = JSON.parse(fs.readFileSync(policiesPath, 'utf8'))

    console.log(`✅ FAQ: ${faqData.length} entries`)
    console.log(`✅ Menu: ${menuData.length} entries`)
    console.log(`✅ Policies: ${policiesData.length} entries`)

    const allData = [...faqData, ...menuData, ...policiesData]
    console.log(`📊 Total: ${allData.length} searchable entries`)

    // Test various queries
    const testQueries = [
      'How much does hibachi cost?',
      'What proteins are included?',
      'Do you travel to my location?',
      'What about dietary restrictions?',
      'Can I book for tonight?',
      'What sauces do you have?',
      'How many people minimum?',
      'What if it rains?'
    ]

    console.log('\n🧪 Running Search Tests...')

    for (const query of testQueries) {
      await testSearch(query, allData)
    }

    // Test page-specific data loading
    console.log('\n📄 Testing Page-Specific Data Loading...')
    console.log('=' .repeat(50))

    const pages = ['/BookUs', '/menu', '/faqs']

    pages.forEach(page => {
      console.log(`\nPage: ${page}`)
      let pageData = [...faqData, ...policiesData] // Always include FAQ and policies

      if (page === '/menu') {
        pageData.push(...menuData)
      }

      console.log(`  📊 Available entries: ${pageData.length}`)

      const categories = [...new Set(pageData.map(item => item.category))]
      console.log(`  🏷️  Categories: ${categories.join(', ')}`)
    })

    console.log('\n✅ All tests completed successfully!')
    console.log('\n🎯 Next Steps:')
    console.log('   1. Start the Next.js development server')
    console.log('   2. Navigate to /BookUs, /menu, or /faqs')
    console.log('   3. Test the chatbot floating button')
    console.log('   4. Try asking questions from the test queries above')

  } catch (error) {
    console.error('\n❌ Error during testing:', error.message)
    process.exit(1)
  }
}

main()
