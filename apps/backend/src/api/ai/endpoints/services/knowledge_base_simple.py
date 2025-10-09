"""
Ultra-Simple Knowledge Base service for production deployment
No ML dependencies - perfect for VPS and local environments
"""

import json
import os
import re
from datetime import datetime
from typing import Any, List, Dict
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class SimpleKnowledgeBaseService:
    """Simple service for managing knowledge base without ML dependencies"""

    def __init__(self):
        self.chunks_cache = {}  # Simple in-memory cache
        self.keywords_index = {}  # Simple keyword index for faster search
        print("KnowledgeBase: Starting ultra-simple knowledge base service (production-ready)")
        
        # Load some basic restaurant knowledge
        self._load_basic_knowledge()

    def _load_basic_knowledge(self):
        """Load basic restaurant knowledge for demo purposes"""
        basic_knowledge = [
            {
                "content": "MyHibachi offers authentic Japanese hibachi dining experience with fresh ingredients and skilled chefs.",
                "keywords": ["hibachi", "japanese", "dining", "fresh", "chef", "authentic"],
                "category": "restaurant_info"
            },
            {
                "content": "We offer booking services for parties of 2-20 people. Reservations can be made online or by phone.",
                "keywords": ["booking", "reservation", "parties", "online", "phone", "table"],
                "category": "booking_info"
            },
            {
                "content": "Our menu includes hibachi grills, sushi, appetizers, and beverages. We accommodate dietary restrictions.",
                "keywords": ["menu", "hibachi", "sushi", "appetizers", "beverages", "dietary", "restrictions"],
                "category": "menu_info"
            },
            {
                "content": "We are open Monday-Sunday from 11 AM to 10 PM. Kitchen closes 30 minutes before closing time.",
                "keywords": ["hours", "open", "monday", "sunday", "11am", "10pm", "kitchen", "closing"],
                "category": "hours_info"
            }
        ]
        
        for i, knowledge in enumerate(basic_knowledge):
            chunk_id = str(uuid4())
            self.chunks_cache[chunk_id] = {
                "content": knowledge["content"],
                "metadata": {
                    "category": knowledge["category"],
                    "keywords": knowledge["keywords"]
                },
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Build keyword index
            for keyword in knowledge["keywords"]:
                if keyword not in self.keywords_index:
                    self.keywords_index[keyword] = []
                self.keywords_index[keyword].append(chunk_id)

    async def search_knowledge_base(
        self, query: str, limit: int = 10, min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Enhanced text search with keyword matching"""
        results = []
        
        # Normalize query
        query_words = re.findall(r'\w+', query.lower())
        
        # Score chunks based on keyword and content matching
        for chunk_id, chunk_data in self.chunks_cache.items():
            content = chunk_data.get('content', '').lower()
            keywords = chunk_data.get('metadata', {}).get('keywords', [])
            
            # Calculate score
            keyword_matches = sum(1 for word in query_words if word in keywords)
            content_matches = sum(1 for word in query_words if word in content)
            
            # Weight keyword matches higher than content matches
            total_score = (keyword_matches * 2 + content_matches) / (len(query_words) * 2) if query_words else 0
            
            if total_score >= min_score:
                results.append({
                    'id': chunk_id,
                    'content': chunk_data.get('content', ''),
                    'metadata': chunk_data.get('metadata', {}),
                    'score': total_score,
                    'match_type': 'keyword' if keyword_matches > 0 else 'content'
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    async def add_knowledge_chunk(
        self, content: str, metadata: Dict[str, Any] = None
    ) -> str:
        """Add a knowledge chunk to the cache"""
        chunk_id = str(uuid4())
        
        # Extract keywords from content if not provided
        if not metadata or 'keywords' not in metadata:
            keywords = self._extract_keywords(content)
            if not metadata:
                metadata = {}
            metadata['keywords'] = keywords
        
        self.chunks_cache[chunk_id] = {
            'content': content,
            'metadata': metadata,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Update keyword index
        for keyword in metadata.get('keywords', []):
            if keyword not in self.keywords_index:
                self.keywords_index[keyword] = []
            self.keywords_index[keyword].append(chunk_id)
        
        return chunk_id

    def _extract_keywords(self, content: str) -> List[str]:
        """Simple keyword extraction from content"""
        # Remove common words and extract meaningful terms
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        words = re.findall(r'\w+', content.lower())
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        # Return unique keywords, limit to 10
        return list(dict.fromkeys(keywords))[:10]

    async def update_knowledge_chunk(
        self, chunk_id: str, content: str = None, metadata: Dict[str, Any] = None
    ):
        """Update a knowledge chunk"""
        if chunk_id in self.chunks_cache:
            if content is not None:
                self.chunks_cache[chunk_id]['content'] = content
                # Re-extract keywords if content changed
                if metadata is None or 'keywords' not in metadata:
                    keywords = self._extract_keywords(content)
                    self.chunks_cache[chunk_id]['metadata']['keywords'] = keywords
            
            if metadata is not None:
                self.chunks_cache[chunk_id]['metadata'].update(metadata)
            
            self.chunks_cache[chunk_id]['updated_at'] = datetime.utcnow().isoformat()

    async def delete_knowledge_chunk(self, chunk_id: str):
        """Delete a knowledge chunk"""
        if chunk_id in self.chunks_cache:
            # Remove from keyword index
            keywords = self.chunks_cache[chunk_id].get('metadata', {}).get('keywords', [])
            for keyword in keywords:
                if keyword in self.keywords_index:
                    self.keywords_index[keyword] = [cid for cid in self.keywords_index[keyword] if cid != chunk_id]
                    if not self.keywords_index[keyword]:
                        del self.keywords_index[keyword]
            
            del self.chunks_cache[chunk_id]

    async def get_chunk_count(self) -> int:
        """Get total number of chunks"""
        return len(self.chunks_cache)

    async def clear_knowledge_base(self):
        """Clear all knowledge base data"""
        self.chunks_cache.clear()
        self.keywords_index.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "total_chunks": len(self.chunks_cache),
            "total_keywords": len(self.keywords_index),
            "has_index": True,
            "encoder_model": "simple_keyword_matching",
            "embedding_dim": 0,
            "service_type": "simple_production",
            "vps_compatible": True
        }


# Global service instance
kb_service = SimpleKnowledgeBaseService()