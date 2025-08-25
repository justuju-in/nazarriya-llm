#!/usr/bin/env python3
"""
Script to ingest documents into the Nazarriya RAG system.
Usage: python ingest_documents.py <document_path1> <document_path2> ...
"""

import sys
import os
import requests
from pathlib import Path


def ingest_documents(file_paths):
    """Ingest documents into the RAG system"""
    if not file_paths:
        print("No file paths provided")
        return
    
    # Validate file paths and remove duplicates
    valid_paths = []
    seen_paths = set()
    
    for path in file_paths:
        file_path = Path(path)
        
        # Skip if we've already seen this path
        if str(file_path) in seen_paths:
            print(f"Skipping duplicate: {path}")
            continue
            
        if not file_path.exists():
            print(f"Warning: File not found: {path}")
            continue
        
        if file_path.suffix.lower() not in ['.pdf', '.html', '.htm']:
            print(f"Warning: Unsupported file type: {path}")
            continue
        
        valid_paths.append(str(file_path))
        seen_paths.add(str(file_path))
    
    if not valid_paths:
        print("No valid files to ingest")
        return
    
    print(f"Ingesting {len(valid_paths)} documents...")
    print("Files to be ingested:")
    for path in valid_paths:
        print(f"  - {path}")
    
    try:
        # Call the ingest endpoint
        response = requests.post(
            "http://localhost:8001/rag/ingest",
            json=valid_paths,
            timeout=60.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! {result['message']}")
            print(f"Files processed: {result['documents_processed']}")
            print(f"Chunks created: {result['chunks_created']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to LLM service. Make sure it's running on port 8001.")
    except Exception as e:
        print(f"Error: {str(e)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_documents.py <document_path1> <document_path2> ...")
        print("Example: python ingest_documents.py doc1.pdf doc2.html doc3.pdf")
        print("\nOr use glob patterns:")
        print("python ingest_documents.py data/pdfs/*.pdf data/html/*.html")
        sys.exit(1)
    
    file_paths = sys.argv[1:]
    ingest_documents(file_paths)


if __name__ == "__main__":
    main()
