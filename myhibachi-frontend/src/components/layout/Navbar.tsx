'use client'

import Link from 'next/link'
import { useState } from 'react'
import Image from 'next/image'
import '@/styles/navbar.css'

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <nav className="navbar navbar-expand-lg custom-navbar">
      <div className="container navbar-container">
        <Link href="/" className="navbar-brand navbar-brand-custom">
          <Image 
            src="/My Hibachi logo.png" 
            alt="My Hibachi Chef Logo" 
            width={70}
            height={70}
            className="navbar-logo"
          />
          <span className="brand-text">My Hibachi Chef</span>
        </Link>
        
        <button 
          className="navbar-toggler navbar-toggler-custom d-lg-none" 
          type="button" 
          onClick={() => setIsOpen(!isOpen)}
          aria-controls="navbarNav"
          aria-expanded={isOpen}
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        
        <div className={`navbar-collapse ${isOpen ? 'show' : ''}`} id="navbarNav">
          <ul className="navbar-nav navbar-nav-custom ms-auto">{/* Changed to ms-auto for Bootstrap 5 */}
            <li className="nav-item">
              <Link href="/" className="nav-link nav-link-custom active">
                <i className="bi bi-house-fill nav-icon"></i>
                <span className="nav-text">About</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link href="/menu" className="nav-link nav-link-custom">
                <i className="bi bi-card-list nav-icon"></i>
                <span className="nav-text">Menu</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link href="/quote" className="nav-link nav-link-custom">
                <i className="bi bi-calculator nav-icon"></i>
                <span className="nav-text">Get Quote</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link href="/BookUs" className="nav-link nav-link-custom">
                <i className="bi bi-calendar-check nav-icon"></i>
                <span className="nav-text">Book Us</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link href="/faqs" className="nav-link nav-link-custom">
                <i className="bi bi-question-circle nav-icon"></i>
                <span className="nav-text">FAQs</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link href="/contact" className="nav-link nav-link-custom">
                <i className="bi bi-chat-dots-fill nav-icon"></i>
                <span className="nav-text">Contact</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link href="/blog" className="nav-link nav-link-custom">
                <i className="bi bi-journal-text nav-icon"></i>
                <span className="nav-text">Blog</span>
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  )
}
