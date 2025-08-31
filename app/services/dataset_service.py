import logging
from typing import List, Dict, Any, Optional, Tuple
import json
from pathlib import Path
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class DatasetService:
    """Service for managing predefined responses and datasets"""
    
    def __init__(self, dataset_file_path: str = "data/dataset.json"):
        self.dataset_file_path = Path(dataset_file_path)
        self.dataset_items = []
        self.load_dataset()
        
        logger.info(f"Dataset service initialized with {len(self.dataset_items)} items")
    
    def load_dataset(self):
        """Load dataset from JSON file"""
        try:
            if self.dataset_file_path.exists():
                with open(self.dataset_file_path, 'r', encoding='utf-8') as f:
                    self.dataset_items = json.load(f)
                logger.info(f"Loaded {len(self.dataset_items)} items from {self.dataset_file_path}")
            else:
                logger.info(f"Dataset file not found at {self.dataset_file_path}, starting with empty dataset")
                self.dataset_items = []
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            self.dataset_items = []
    
    def save_dataset(self):
        """Save dataset to JSON file"""
        try:
            self.dataset_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.dataset_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.dataset_items, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved dataset to {self.dataset_file_path}")
        except Exception as e:
            logger.error(f"Error saving dataset: {str(e)}")
    
    def ingest_dataset_file(self, file_path: str) -> Dict[str, Any]:
        """Ingest an entire dataset file (JSON format)"""
        try:
            # Try to find the file in multiple locations
            source_file = self._find_source_file(file_path)
            if not source_file:
                raise FileNotFoundError(f"Dataset file not found: {file_path}")
            
            logger.info(f"Found source file at: {source_file}")
            
            # Read and parse the source file
            with open(source_file, 'r', encoding='utf-8') as f:
                new_items = json.load(f)
            
            if not isinstance(new_items, list):
                raise ValueError("Dataset file must contain a list of items")
            
            # Copy file to data directory if it's not already there
            data_file = self._ensure_file_in_data_directory(source_file)
            logger.info(f"Using dataset file at: {data_file}")
            
            # Clear existing items and replace with new ones
            self.dataset_items = []
            added_count = 0
            
            for item in new_items:
                if self._validate_item(item):
                    self.dataset_items.append(item)
                    added_count += 1
                else:
                    logger.warning(f"Skipping invalid item: {item.get('question', 'Unknown')[:50]}...")
            
            # Save updated dataset
            self.save_dataset()
            
            logger.info(f"Ingested {added_count} items from {source_file.name}")
            return {
                "message": f"Successfully ingested {added_count} items",
                "file_processed": str(source_file),
                "data_file_location": str(data_file),
                "items_added": added_count,
                "total_items": len(self.dataset_items),
                "auto_copied": source_file != data_file
            }
            
        except Exception as e:
            logger.error(f"Error ingesting dataset file: {str(e)}")
            raise
    
    def _find_source_file(self, file_path: str) -> Optional[Path]:
        """Find the source file in multiple possible locations"""
        possible_paths = [
            Path(file_path),  # Direct path
            Path.cwd() / file_path,  # Current working directory
            Path(__file__).parent.parent.parent / file_path,  # Project root
            Path(__file__).parent.parent.parent / "data" / file_path  # Data directory
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found file at: {path}")
                return path
        
        logger.warning(f"File not found in any of these locations: {[str(p) for p in possible_paths]}")
        return None
    
    def _ensure_file_in_data_directory(self, source_file: Path) -> Path:
        """Ensure the file exists in the data directory, copy if necessary"""
        data_dir = Path(__file__).parent.parent.parent / "data"
        data_file = data_dir / source_file.name
        
        # If source is already in data directory, use it directly
        if source_file.parent == data_dir:
            logger.info(f"File already in data directory: {data_file}")
            return data_file
        
        # Copy file to data directory
        try:
            import shutil
            shutil.copy2(source_file, data_file)
            logger.info(f"Copied {source_file.name} to data directory: {data_file}")
        except Exception as e:
            logger.warning(f"Could not copy file to data directory: {str(e)}")
            # Continue with source file if copy fails
            return source_file
        
        return data_file
    
    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate a dataset item"""
        required_fields = ['question', 'answer']
        return all(field in item and item[field] for field in required_fields)
    
    def add_item(self, question: str, answer: str, keywords: List[str] = None, 
                 category: str = None, source: str = None):
        """Add a new item to the dataset"""
        # Auto-generate keywords from question if not provided
        if keywords is None:
            keywords = self._auto_generate_keywords(question)
        
        # Use defaults if not provided
        category = category or "general"
        source = source or "manual"
        
        item = {
            "question": question,
            "answer": answer,
            "keywords": keywords,
            "category": category,
            "source": source
        }
        
        self.dataset_items.append(item)
        self.save_dataset()
        logger.info(f"Added new item for category: {category}")
    
    def _auto_generate_keywords(self, question: str) -> List[str]:
        """Automatically generate keywords from the question"""
        # Simple keyword extraction - split by common delimiters and filter
        import re
        
        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', question.lower())
        
        # Filter out common stop words
        stop_words = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
            'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
            'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
            'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
            'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by',
            'for', 'with', 'against', 'between', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
            'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain',
            'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn',
            'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn'
        }
        
        # Filter out stop words and short words, keep meaningful words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Limit to top 8 most relevant keywords
        return keywords[:8]
    
    def find_best_match(self, query: str, threshold: float = 0.6) -> Optional[Dict[str, Any]]:
        """Find the best matching item for a given query"""
        if not self.dataset_items:
            return None
        
        best_match = None
        best_score = 0
        
        for item in self.dataset_items:
            # Calculate similarity score
            score = self._calculate_similarity(query, item["question"])
            
            # Also check keywords
            keyword_score = self._calculate_keyword_similarity(query, item.get("keywords", []))
            
            # Combined score (question similarity + keyword bonus)
            combined_score = score + (keyword_score * 0.3)
            
            if combined_score > best_score and combined_score >= threshold:
                best_score = combined_score
                best_match = item
                best_match["similarity_score"] = combined_score
        
        if best_match:
            logger.info(f"Found dataset match with score {best_score:.2f} for query: {query[:50]}...")
        
        return best_match
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        # Convert to lowercase for better matching
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # Use SequenceMatcher for similarity
        similarity = SequenceMatcher(None, text1_lower, text2_lower).ratio()
        
        # Bonus for exact keyword matches
        words1 = set(text1_lower.split())
        words2 = set(text2_lower.split())
        common_words = words1.intersection(words2)
        
        if len(common_words) > 0:
            word_bonus = len(common_words) / max(len(words1), len(words2)) * 0.2
            similarity += word_bonus
        
        return min(similarity, 1.0)
    
    def _calculate_keyword_similarity(self, query: str, keywords: List[str]) -> float:
        """Calculate similarity based on keywords"""
        if not keywords:
            return 0.0
        
        query_lower = query.lower()
        matches = 0
        
        for keyword in keywords:
            if keyword.lower() in query_lower:
                matches += 1
        
        return matches / len(keywords) if keywords else 0.0
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all dataset items"""
        return self.dataset_items
    
    def get_items_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get items by category"""
        return [item for item in self.dataset_items if item.get("category") == category]
    
    def delete_item(self, index: int) -> bool:
        """Delete an item by index"""
        try:
            if 0 <= index < len(self.dataset_items):
                deleted = self.dataset_items.pop(index)
                self.save_dataset()
                logger.info(f"Deleted item: {deleted['question'][:50]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting item: {str(e)}")
            return False
    
    def update_item(self, index: int, **kwargs) -> bool:
        """Update an item by index"""
        try:
            if 0 <= index < len(self.dataset_items):
                for key, value in kwargs.items():
                    if key in self.dataset_items[index]:
                        self.dataset_items[index][key] = value
                
                self.save_dataset()
                logger.info(f"Updated item at index {index}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating item: {str(e)}")
            return False
    
    def clear_dataset(self) -> bool:
        """Clear all items from the dataset"""
        try:
            self.dataset_items = []
            self.save_dataset()
            logger.info("Dataset cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing dataset: {str(e)}")
            return False
    

