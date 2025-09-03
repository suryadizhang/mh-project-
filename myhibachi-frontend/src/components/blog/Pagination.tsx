'use client'

import { ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react'
import React from 'react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  className?: string
}

export default function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  className = ''
}: PaginationProps) {
  if (totalPages <= 1) return null

  const generatePageNumbers = () => {
    const pages = []
    const showEllipsis = totalPages > 7

    if (!showEllipsis) {
      // Show all pages if 7 or fewer
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      // Always show first page
      pages.push(1)

      // Show ellipsis or pages near current page
      if (currentPage <= 4) {
        // Show 1, 2, 3, 4, 5, ..., last
        for (let i = 2; i <= Math.min(5, totalPages - 1); i++) {
          pages.push(i)
        }
        if (totalPages > 5) {
          pages.push('ellipsis1')
        }
      } else if (currentPage >= totalPages - 3) {
        // Show 1, ..., last-4, last-3, last-2, last-1, last
        pages.push('ellipsis1')
        for (let i = Math.max(2, totalPages - 4); i <= totalPages - 1; i++) {
          pages.push(i)
        }
      } else {
        // Show 1, ..., current-1, current, current+1, ..., last
        pages.push('ellipsis1')
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i)
        }
        pages.push('ellipsis2')
      }

      // Always show last page (unless it's already included)
      if (totalPages > 1 && !pages.includes(totalPages)) {
        pages.push(totalPages)
      }
    }

    return pages
  }

  const pageNumbers = generatePageNumbers()

  const handlePageClick = (page: number | string) => {
    if (typeof page === 'number' && page !== currentPage) {
      onPageChange(page)
    }
  }

  const handlePrevious = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1)
    }
  }

  const handleNext = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1)
    }
  }

  return (
    <nav
      className={`flex items-center justify-center space-x-1 ${className}`}
      aria-label="Pagination"
    >
      {/* Previous Button */}
      <button
        onClick={handlePrevious}
        disabled={currentPage === 1}
        className={`
          inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors
          ${
            currentPage === 1
              ? 'text-slate-400 cursor-not-allowed bg-slate-50'
              : 'text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-slate-900 shadow-sm'
          }
        `}
        aria-label="Go to previous page"
      >
        <ChevronLeft className="w-4 h-4 mr-1" />
        Previous
      </button>

      {/* Page Numbers */}
      <div className="flex items-center space-x-1">
        {pageNumbers.map((page, index) => (
          <React.Fragment key={index}>
            {typeof page === 'string' ? (
              <span className="px-3 py-2 text-slate-400">
                <MoreHorizontal className="w-4 h-4" />
              </span>
            ) : (
              <button
                onClick={() => handlePageClick(page)}
                className={`
                  px-3 py-2 text-sm font-medium rounded-lg transition-colors min-w-[40px]
                  ${
                    page === currentPage
                      ? 'bg-slate-800 text-white border border-slate-800 shadow-sm'
                      : 'text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-slate-900 shadow-sm'
                  }
                `}
                aria-label={`Go to page ${page}`}
                aria-current={page === currentPage ? 'page' : undefined}
              >
                {page}
              </button>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Next Button */}
      <button
        onClick={handleNext}
        disabled={currentPage === totalPages}
        className={`
          inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors
          ${
            currentPage === totalPages
              ? 'text-slate-400 cursor-not-allowed bg-slate-50'
              : 'text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-slate-900 shadow-sm'
          }
        `}
        aria-label="Go to next page"
      >
        Next
        <ChevronRight className="w-4 h-4 ml-1" />
      </button>

      {/* Page Info */}
      <div className="hidden sm:block ml-6">
        <p className="text-sm text-slate-600">
          Page <span className="font-medium text-slate-900">{currentPage}</span> of{' '}
          <span className="font-medium text-slate-900">{totalPages}</span>
        </p>
      </div>
    </nav>
  )
}
