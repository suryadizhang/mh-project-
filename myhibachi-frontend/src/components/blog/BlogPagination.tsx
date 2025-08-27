'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react'
import type { BlogPost } from '@/data/blogPosts'

interface BlogPaginationProps {
  posts: BlogPost[]
  postsPerPage?: number
  onPageChange: (paginatedPosts: BlogPost[], currentPage: number, totalPages: number) => void
}

export default function BlogPagination({ posts, postsPerPage = 9, onPageChange }: BlogPaginationProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [loadMore, setLoadMore] = useState(false)
  
  const totalPages = Math.ceil(posts.length / postsPerPage)
  const startIndex = (currentPage - 1) * postsPerPage
  const endIndex = loadMore ? currentPage * postsPerPage : startIndex + postsPerPage
  const currentPosts = posts.slice(0, endIndex)
  
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    setLoadMore(false)
    const start = (page - 1) * postsPerPage
    const end = start + postsPerPage
    const paginatedPosts = posts.slice(start, end)
    onPageChange(paginatedPosts, page, totalPages)
    
    // Scroll to top of blog section
    document.querySelector('[data-page="blog"] .blog-section')?.scrollIntoView({ 
      behavior: 'smooth' 
    })
  }
  
  const handleLoadMore = () => {
    const nextPage = currentPage + 1
    setCurrentPage(nextPage)
    setLoadMore(true)
    const morePosts = posts.slice(0, nextPage * postsPerPage)
    onPageChange(morePosts, nextPage, totalPages)
  }
  
  const resetPagination = () => {
    setCurrentPage(1)
    setLoadMore(false)
    const firstPagePosts = posts.slice(0, postsPerPage)
    onPageChange(firstPagePosts, 1, totalPages)
  }
  
  // Update when posts change
  useEffect(() => {
    resetPagination()
  }, [posts.length]) // eslint-disable-line react-hooks/exhaustive-deps
  
  if (posts.length <= postsPerPage) {
    return null
  }
  
  return (
    <div className="blog-pagination-container">
      {loadMore ? (
        // Load More Mode
        <div className="blog-load-more">
          <p className="text-sm text-gray-600 mb-4">
            Showing {currentPosts.length} of {posts.length} articles
          </p>
          
          <div className="flex gap-4 justify-center">
            {currentPage < totalPages && (
              <button
                onClick={handleLoadMore}
                className="blog-load-more-btn"
              >
                Load More Articles
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
            
            <button
              onClick={resetPagination}
              className="blog-pagination-btn"
            >
              <RotateCcw className="w-4 h-4" />
              Start Over
            </button>
          </div>
        </div>
      ) : (
        // Traditional Pagination
        <div className="blog-pagination">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="blog-pagination-btn"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>
          
          {/* Page Numbers */}
          {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
            let pageNum
            if (totalPages <= 5) {
              pageNum = i + 1
            } else if (currentPage <= 3) {
              pageNum = i + 1
            } else if (currentPage >= totalPages - 2) {
              pageNum = totalPages - 4 + i
            } else {
              pageNum = currentPage - 2 + i
            }
            
            return (
              <button
                key={pageNum}
                onClick={() => handlePageChange(pageNum)}
                className={`blog-pagination-btn ${currentPage === pageNum ? 'active' : ''}`}
              >
                {pageNum}
              </button>
            )
          })}
          
          {totalPages > 5 && currentPage < totalPages - 2 && (
            <>
              <span className="blog-pagination-dots">...</span>
              <button
                onClick={() => handlePageChange(totalPages)}
                className="blog-pagination-btn"
              >
                {totalPages}
              </button>
            </>
          )}
          
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="blog-pagination-btn"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
          
          {/* Load More Option */}
          <button
            onClick={() => setLoadMore(true)}
            className="blog-pagination-btn ml-4"
            style={{ marginLeft: '1rem' }}
          >
            Switch to Load More
          </button>
        </div>
      )}
      
      {/* Results Summary */}
      <div className="text-center mt-4">
        <p className="text-sm text-gray-600">
          {loadMore 
            ? `Showing ${currentPosts.length} of ${posts.length} articles`
            : `Page ${currentPage} of ${totalPages} • ${posts.length} total articles`
          }
        </p>
      </div>
    </div>
  )
}
