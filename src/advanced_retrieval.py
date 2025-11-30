"""
Advanced Retrieval Techniques - Cải thiện chất lượng trả lời
Bao gồm: Re-ranking, Hybrid Search, Query Expansion
"""

from typing import List, Dict
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank, LLMChainExtractor
from langchain_anthropic import ChatAnthropic
import os


def create_reranking_retriever(base_retriever, anthropic_api_key=None):
    """
    Tạo retriever với re-ranking sử dụng Claude
    
    Flow: 
    1. Lấy 20 chunks từ vector store
    2. Claude đánh giá và xếp hạng lại từng chunk
    3. Trả về 6 chunks tốt nhất
    
    Args:
        base_retriever: Retriever gốc từ vector store
        anthropic_api_key: Claude API key
    
    Returns:
        reranking_retriever: Retriever với re-ranking
    """
    if not anthropic_api_key:
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Tạo LLM compressor với Claude
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        temperature=0,
        api_key=anthropic_api_key
    )
    
    compressor = LLMChainExtractor.from_llm(llm)
    
    # Wrap base retriever với compression
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )
    
    return compression_retriever


def expand_query_vietnamese(question: str) -> List[str]:
    """
    Mở rộng câu hỏi với từ đồng nghĩa tiếng Việt
    
    Ví dụ: "Định luật nhiệt động" → ["Định luật nhiệt động", "Nguyên lý nhiệt học", 
                                      "Quy luật nhiệt"]
    
    Args:
        question: Câu hỏi gốc
    
    Returns:
        queries: List các câu hỏi mở rộng
    """
    # Dictionary từ đồng nghĩa chuyên ngành Vật lý
    synonyms = {
        'định luật': ['nguyên lý', 'quy luật', 'định lý'],
        'nhiệt động': ['nhiệt học', 'nhiệt động lực học'],
        'khí lý tưởng': ['khí hoàn hảo', 'khí ideal'],
        'từ trường': ['từ tính', 'trường từ'],
        'hạt nhân': ['nguyên tử hạt nhân', 'nhân nguyên tử'],
        'phóng xạ': ['bức xạ', 'tia phóng xạ', 'hoạt động phóng xạ'],
        'chu kỳ': ['thời kỳ', 'tuần hoàn'],
        'bán rã': ['phân rã', 'suy giảm'],
        'năng lượng': ['động năng', 'thế năng', 'công suất'],
        'nhiệt độ': ['độ nóng', 'temperature'],
        'áp suất': ['áp lực', 'pressure'],
        'thể tích': ['dung tích', 'volume'],
        'công': ['công việc', 'work'],
        'nhiệt lượng': ['nhiệt', 'heat', 'lượng nhiệt'],
    }
    
    queries = [question]
    question_lower = question.lower()
    
    # Thay thế từng từ khóa bằng từ đồng nghĩa
    for word, syns in synonyms.items():
        if word in question_lower:
            for syn in syns:
                expanded_q = question_lower.replace(word, syn)
                queries.append(expanded_q)
    
    # Giới hạn 5 queries để không quá chậm
    return queries[:5]


class HybridSearchRetriever:
    """
    Kết hợp Vector Search (semantic) + Keyword Search (BM25)
    
    Vector Search: Hiểu nghĩa ("nhiệt độ" ≈ "độ nóng")
    Keyword Search: Tìm từ khóa chính xác ("PV = nRT")
    """
    
    def __init__(self, vector_store, documents):
        """
        Args:
            vector_store: FAISS/Pinecone vector store
            documents: List các document chunks (cần cho BM25)
        """
        self.vector_store = vector_store
        self.documents = documents
        self.bm25 = None
        self._init_bm25()
    
    def _init_bm25(self):
        """Khởi tạo BM25 keyword search"""
        try:
            from rank_bm25 import BM25Okapi
            import jieba
            
            # Tách từ cho mỗi document
            tokenized_docs = [
                list(jieba.cut(doc['text'])) for doc in self.documents
            ]
            self.bm25 = BM25Okapi(tokenized_docs)
            print("BM25 Keyword Search đã sẵn sàng")
        except ImportError as e:
            print(f"Cần cài đặt: pip install rank-bm25 jieba (Lỗi: {e})")
            self.bm25 = None
        except Exception as e:
            print(f"Lỗi khởi tạo BM25: {e}")
            self.bm25 = None
    
    def search(self, query: str, k: int = 8) -> List[Dict]:
        """
        Hybrid search: Kết hợp vector + keyword
        
        Args:
            query: Câu hỏi
            k: Số chunks cần lấy
        
        Returns:
            results: List chunks được ranked
        """
        results = {}
        
        # 1. Vector search (semantic similarity)
        vector_docs = self.vector_store.similarity_search_with_score(query, k=k)
        for doc, score in vector_docs:
            doc_id = f"{doc.metadata['source']}_{doc.metadata['chunk_id']}"
            results[doc_id] = {
                'doc': doc,
                'vector_score': score,
                'bm25_score': 0
            }
        
        # 2. BM25 keyword search
        if self.bm25:
            import jieba
            tokenized_query = list(jieba.cut(query))
            bm25_scores = self.bm25.get_scores(tokenized_query)
            
            # Top k results từ BM25
            top_bm25_indices = sorted(
                range(len(bm25_scores)), 
                key=lambda i: bm25_scores[i], 
                reverse=True
            )[:k]
            
            for idx in top_bm25_indices:
                doc_data = self.documents[idx]
                doc_id = f"{doc_data['source']}_{doc_data['chunk_id']}"
                
                if doc_id in results:
                    results[doc_id]['bm25_score'] = bm25_scores[idx]
                else:
                    # Create pseudo document object
                    from langchain.schema import Document
                    doc = Document(
                        page_content=doc_data['text'],
                        metadata={
                            'source': doc_data['source'],
                            'chunk_id': doc_data['chunk_id']
                        }
                    )
                    results[doc_id] = {
                        'doc': doc,
                        'vector_score': 0,
                        'bm25_score': bm25_scores[idx]
                    }
        
        # 3. Kết hợp điểm số (weighted average)
        final_results = []
        for doc_id, data in results.items():
            # Normalize scores về [0, 1]
            vector_norm = 1 / (1 + data['vector_score']) if data['vector_score'] > 0 else 0
            bm25_norm = data['bm25_score'] / 100 if data['bm25_score'] > 0 else 0
            
            # Weighted combination: 70% vector + 30% BM25
            combined_score = 0.7 * vector_norm + 0.3 * bm25_norm
            
            final_results.append({
                'doc': data['doc'],
                'score': combined_score
            })
        
        # Sắp xếp theo điểm tổng hợp
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        return [r['doc'] for r in final_results[:k]]


def create_hybrid_retriever(vector_store, documents):
    """
    Wrapper để tạo hybrid retriever tương thích với LangChain
    
    Args:
        vector_store: FAISS/Pinecone vector store
        documents: List chunks
    
    Returns:
        CustomRetriever với hybrid search
    """
    from langchain.schema.retriever import BaseRetriever
    from langchain.callbacks.manager import CallbackManagerForRetrieverRun
    from typing import List
    from langchain.schema import Document
    
    class CustomHybridRetriever(BaseRetriever):
        hybrid_searcher: HybridSearchRetriever
        k: int = 8
        
        def _get_relevant_documents(
            self, 
            query: str, 
            *, 
            run_manager: CallbackManagerForRetrieverRun = None
        ) -> List[Document]:
            return self.hybrid_searcher.search(query, k=self.k)
    
    hybrid_searcher = HybridSearchRetriever(vector_store, documents)
    return CustomHybridRetriever(hybrid_searcher=hybrid_searcher, k=8)


# Test function
if __name__ == "__main__":
    # Test query expansion
    question = "Định luật I nhiệt động là gì?"
    expanded = expand_query_vietnamese(question)
    print("Query Expansion Test:")
    print(f"Original: {question}")
    print(f"Expanded: {expanded}")
