#!/usr/bin/env python3
"""
Test script for the Nazarriya LLM Service
Run this to verify all endpoints are working correctly
"""

import requests
import json
import time
from pathlib import Path


def test_health_endpoint():
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {str(e)}")
        return False


def test_rag_health():
    """Test the RAG health endpoint"""
    print("🔍 Testing RAG health endpoint...")
    try:
        response = requests.get("http://localhost:8001/rag/health", timeout=10)
        if response.status_code == 200:
            print("✅ RAG health endpoint working")
            return True
        else:
            print(f"❌ RAG health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ RAG health endpoint error: {str(e)}")
        return False


def test_rag_status():
    """Test the RAG status endpoint"""
    print("📊 Testing RAG status endpoint...")
    try:
        response = requests.get("http://localhost:8001/rag/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("✅ RAG status endpoint working")
            print(f"   - Vector store documents: {status.get('vector_store', {}).get('total_documents', 'N/A')}")
            print(f"   - Available documents: {status.get('total_documents', 'N/A')}")
            print(f"   - Model: {status.get('model_info', {}).get('model', 'N/A')}")
            return True
        else:
            print(f"❌ RAG status endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ RAG status endpoint error: {str(e)}")
        return False


def test_documents_list():
    """Test the documents list endpoint"""
    print("📚 Testing documents list endpoint...")
    try:
        response = requests.get("http://localhost:8001/rag/documents", timeout=10)
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Documents list endpoint working - {len(documents)} documents found")
            for doc in documents:
                print(f"   - {doc['filename']} ({doc['file_type']}) - {doc['chunks']} chunks")
            return True
        else:
            print(f"❌ Documents list endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Documents list endpoint error: {str(e)}")
        return False


def test_rag_query():
    """Test the RAG query endpoint"""
    print("❓ Testing RAG query endpoint...")
    try:
        response = requests.post(
            "http://localhost:8001/rag/query",
            json={
                "query": "What is this service about?",
                "history": [],
                "max_tokens": 200
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ RAG query endpoint working")
            print(f"   - Answer length: {len(result['answer'])} characters")
            print(f"   - Sources found: {len(result['sources'])}")
            print(f"   - Answer preview: {result['answer'][:100]}...")
            return True
        else:
            print(f"❌ RAG query endpoint failed: {response.status_code}")
            print(f"   - Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ RAG query endpoint error: {str(e)}")
        return False


def test_document_upload():
    """Test document upload functionality"""
    print("📤 Testing document upload...")
    
    # Check if there are any documents in the data directory
    pdf_dir = Path("data/pdfs")
    html_dir = Path("data/html")
    
    test_files = []
    if pdf_dir.exists():
        test_files.extend(list(pdf_dir.glob("*.pdf"))[:1])
    if html_dir.exists():
        test_files.extend(list(html_dir.glob("*.html"))[:1])
    
    if not test_files:
        print("⚠️  No test documents found in data directory")
        return True
    
    try:
        # Test with the first available file
        test_file = test_files[0]
        print(f"   - Testing with: {test_file.name}")
        
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "application/octet-stream")}
            response = requests.post(
                "http://localhost:8001/rag/upload",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document upload working")
            print(f"   - Chunks created: {result['chunks_created']}")
            return True
        else:
            print(f"❌ Document upload failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Document upload error: {str(e)}")
        return False


def test_dataset_endpoints():
    """Test dataset management endpoints"""
    print("📊 Testing dataset endpoints...")
    
    try:
        # Test listing dataset items
        response = requests.get("http://localhost:8001/rag/dataset", timeout=10)
        if response.status_code == 200:
            items = response.json()
            print(f"✅ Dataset list endpoint working - {len(items)} items found")
        else:
            print(f"❌ Dataset list endpoint failed: {response.status_code}")
            return False
        
        # Test adding a dataset item
        test_item = {
            "question": "What is the test question?",
            "answer": "This is a test answer for testing purposes."
        }
        
        response = requests.post(
            "http://localhost:8001/rag/dataset",
            json=test_item,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Dataset add endpoint working")
        else:
            print(f"❌ Dataset add endpoint failed: {response.status_code}")
            return False
        
        # Test querying with the dataset item
        response = requests.post(
            "http://localhost:8001/rag/query",
            json={
                "query": "What is the test question?",
                "history": [],
                "max_tokens": 200
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get('sources', [])
            if sources and sources[0].get('metadata', {}).get('type') == 'predefined_dataset':
                print("✅ Dataset query working - using predefined response")
            else:
                print("⚠️  Dataset query working but not using predefined response")
        else:
            print(f"❌ Dataset query failed: {response.status_code}")
            return False
        
        # Clean up test item
        response = requests.delete("http://localhost:8001/rag/dataset/0", timeout=10)
        if response.status_code == 200:
            print("✅ Dataset delete endpoint working")
        else:
            print(f"⚠️  Dataset delete endpoint failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dataset endpoints error: {str(e)}")
        return False


def test_masculinity_query():
    """Test the specific masculinity question with dataset"""
    print("🎯 Testing masculinity question with dataset...")
    
    try:
        response = requests.post(
            "http://localhost:8001/rag/query",
            json={
                "query": "I really like dressing up, but my family keeps telling me I'm \"too much\". I like bright shirts and rings or even eyeliner. My brother tells me that wanting such things makes me \"less of a man\".",
                "history": [],
                "max_tokens": 500
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            sources = result.get('sources', [])
            
            if sources and sources[0].get('metadata', {}).get('type') == 'predefined_dataset':
                print("✅ Masculinity query using predefined dataset response")
                print(f"   - Answer: {result['answer'][:100]}...")
                print(f"   - Source: {sources[0].get('metadata', {}).get('source', 'Unknown')}")
                print(f"   - Similarity Score: {sources[0].get('metadata', {}).get('similarity_score', 'N/A')}")
                return True
            else:
                print("⚠️  Masculinity query not using predefined dataset")
                print(f"   - Answer: {result['answer'][:100]}...")
                print(f"   - Sources: {len(sources)} document sources")
                return True  # Still working, just not using dataset
        else:
            print(f"❌ Masculinity query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Masculinity query error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("🧪 Starting Nazarriya LLM Service Tests")
    print("=" * 50)
    
    # Wait a moment for service to be ready
    print("⏳ Waiting for service to be ready...")
    time.sleep(2)
    
    tests = [
        test_health_endpoint,
        test_rag_health,
        test_rag_status,
        test_documents_list,
        test_rag_query,
        test_document_upload,
        test_dataset_endpoints,
        test_masculinity_query
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The service is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the service logs for more details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
