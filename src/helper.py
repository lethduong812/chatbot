"""
Helper functions để xử lý PDF và xây dựng chatbot
"""

import os
import base64
from io import BytesIO
from pypdf import PdfReader
from pdf2image import convert_from_path
from PIL import Image
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from dotenv import load_dotenv
import anthropic

# Import advanced retrieval techniques
try:
    from src.advanced_retrieval import (
        create_reranking_retriever,
        expand_query_vietnamese,
        create_hybrid_retriever
    )
    ADVANCED_RETRIEVAL_AVAILABLE = True
except ImportError:
    ADVANCED_RETRIEVAL_AVAILABLE = False
    print("Advanced retrieval không khả dụng (cài thêm: pip install rank-bm25 jieba)")

# Load environment variables
load_dotenv()


def extract_images_from_pdf(file_path, page_num):
    """
    Trích xuất hình ảnh từ trang PDF
    
    Args:
        file_path: Đường dẫn đến file PDF
        page_num: Số trang (bắt đầu từ 0)
    
    Returns:
        images: List PIL Images
    """
    try:
        # Poppler path trong project (tự động download)
        poppler_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "poppler", "poppler-24.08.0", "Library", "bin"
        )
        
        images = convert_from_path(
            file_path, 
            first_page=page_num + 1, 
            last_page=page_num + 1,
            dpi=100,  # Giảm từ 150 → 100 DPI (giảm ~40% cost)
            poppler_path=poppler_path if os.path.exists(poppler_path) else None
        )
        return images
    except Exception as e:
        print(f"Lỗi khi trích xuất ảnh từ trang {page_num}: {e}")
        print("Lưu ý: Cần cài Poppler. Xem hướng dẫn trong POPPLER_INSTALL.md")
        return []


def image_to_base64(image):
    """
    Chuyển PIL Image thành base64 string để gửi đến Claude API
    
    Args:
        image: PIL Image object
    
    Returns:
        base64_str: Base64 encoded string
    """
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def analyze_image_with_claude(image, context=""):
    """
    Sử dụng Claude Vision API để phân tích hình ảnh
    
    Args:
        image: PIL Image object
        context: Context text xung quanh ảnh
    
    Returns:
        description: Mô tả chi tiết về ảnh (tiếng Việt)
    """
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Chuyển image sang base64
        image_base64 = image_to_base64(image)
        
        # Prompt cho Claude Vision (tiếng Việt)
        prompt = f"""Bạn là trợ lý phân tích hình ảnh trong sách vật lý tiếng Việt.

Context văn bản xung quanh: {context}

Hãy phân tích chi tiết hình ảnh này và mô tả bằng tiếng Việt:
1. Nếu là SƠ ĐỒ/BIỂU ĐỒ: Mô tả các thành phần, kết nối, quy trình
2. Nếu là CÔNG THỨC TOÁN: OCR chính xác công thức, giải thích ý nghĩa các ký hiệu
3. Nếu là ĐỒ THỊ: Mô tả trục, đơn vị, xu hướng, mối quan hệ biến số
4. Nếu là HÌNH MINH HỌA: Mô tả hiện tượng vật lý, thiết bị, thí nghiệm

Trả lời ngắn gọn, súc tích, tập trung vào thông tin quan trọng."""

        # Gọi Claude Vision API
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )
        
        return message.content[0].text
    
    except Exception as e:
        print(f"Lỗi khi phân tích ảnh với Claude: {e}")
        return None


def load_all_pdfs(data_dir="data", extract_images=True):
    """
    Đọc tất cả file PDF trong thư mục data (bao gồm text + hình ảnh)
    
    Args:
        data_dir: Đường dẫn đến thư mục chứa PDF
        extract_images: True = phân tích ảnh với Claude Vision
    
    Returns:
        documents: List các document với text và metadata
    """
    documents = []
    
    if not os.path.exists(data_dir):
        print(f"Thư mục {data_dir} không tồn tại!")
        return documents
    
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
    
    print(f"Tìm thấy {len(pdf_files)} file PDF")
    if extract_images:
        print("Chế độ: Trích xuất cả TEXT + HÌNH ẢNH (sử dụng Claude Vision)")
    else:
        print("Chế độ: Chỉ trích xuất TEXT")
    
    for pdf_file in pdf_files:
        file_path = os.path.join(data_dir, pdf_file)
        print(f"Đang đọc: {pdf_file}...")
        text = load_pdf(file_path, extract_images=extract_images)
        
        if text:
            documents.append({
                'text': text,
                'source': pdf_file
            })
    
    return documents


def load_pdf(file_path, extract_images=True):
    """
    Đọc và trích xuất text + hình ảnh từ file PDF
    
    Args:
        file_path: Đường dẫn đến file PDF
        extract_images: True = phân tích ảnh với Claude Vision
    
    Returns:
        text: Nội dung text + mô tả hình ảnh từ PDF
    """
    try:
        reader = PdfReader(file_path)
        full_text = ""
        
        for page_num, page in enumerate(reader.pages):
            # Trích xuất text
            page_text = page.extract_text()
            full_text += f"\n--- Trang {page_num + 1} ---\n"
            full_text += page_text
            
            # Trích xuất và phân tích hình ảnh nếu được yêu cầu
            if extract_images:
                images = extract_images_from_pdf(file_path, page_num)
                
                if images:  # Chỉ xử lý nếu có ảnh
                    for img_idx, image in enumerate(images):  # Xử lý TẤT CẢ ảnh
                        print(f"  Đang phân tích ảnh {img_idx + 1} trang {page_num + 1}...")
                        
                        # Lấy context xung quanh (200 ký tự gần nhất)
                        context = page_text[-200:] if page_text else ""
                        
                        # Phân tích ảnh với Claude
                        image_description = analyze_image_with_claude(image, context)
                        
                        if image_description:
                            full_text += f"\n[HÌNH ẢNH {img_idx + 1} - Trang {page_num + 1}]\n"
                            full_text += image_description + "\n"
        
        return full_text
    except Exception as e:
        print(f"Lỗi khi đọc file {file_path}: {e}")
        return ""





def split_text_into_chunks(documents, chunk_size=1000, chunk_overlap=200):
    """
    Chia text thành các chunks nhỏ hơn để xử lý
    
    Args:
        documents: List các document
        chunk_size: Kích thước mỗi chunk
        chunk_overlap: Độ chồng lấp giữa các chunks
    
    Returns:
        chunks: List các text chunks với metadata
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    all_chunks = []
    
    for doc in documents:
        chunks = text_splitter.split_text(doc['text'])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                'text': chunk,
                'source': doc['source'],
                'chunk_id': i
            })
    
    print(f"Đã tạo {len(all_chunks)} chunks từ {len(documents)} documents")
    return all_chunks


def create_embeddings(use_phobert=True):
    """
    Tạo embedding model - Hỗ trợ PhoBERT (tối ưu tiếng Việt) hoặc multilingual
    
    Args:
        use_phobert: True = PhoBERT (tốt cho tiếng Việt), False = multilingual
    
    Returns:
        embeddings: Embedding model
    """
    if use_phobert:
        print("Sử dụng PhoBERT Embeddings (tối ưu cho tiếng Việt)")
        try:
            return HuggingFaceEmbeddings(
                model_name="VoVanPhuc/sup-SimCSE-VietNamese-phobert-base",
                model_kwargs={
                    'device': 'cpu',
                    'trust_remote_code': True
                },
                encode_kwargs={
                    'normalize_embeddings': True,  # Normalize vectors
                    'batch_size': 32  # Batch processing
                }
            )
        except Exception as e:
            print(f"Không thể load PhoBERT: {e}")
            print("Fallback sang multilingual model...")
            use_phobert = False
    
    if not use_phobert:
        print("Sử dụng Multilingual Embeddings (hỗ trợ đa ngôn ngữ)")
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )





def create_vector_store_pinecone(chunks, embeddings, index_name="chatbot-study"):
    """
    Tạo Pinecone vector store (cloud-based, cần API key)
    
    Args:
        chunks: List các text chunks
        embeddings: Embedding model
        index_name: Tên Pinecone index
    
    Returns:
        vector_store: Pinecone vector store
    """
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    
    if not pinecone_api_key:
        print("Không tìm thấy PINECONE_API_KEY!")
        return None
    
    print("Đang tạo Pinecone vector store...")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)
    
    texts = [chunk['text'] for chunk in chunks]
    metadatas = [{'source': chunk['source'], 'chunk_id': chunk['chunk_id']} 
                 for chunk in chunks]
    
    vector_store = PineconeVectorStore.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        index_name=index_name
    )
    
    print(f"Đã tạo Pinecone index: {index_name}")
    return vector_store


def create_chatbot(vector_store, prompt_template, use_memory=True, 
                   use_advanced_retrieval=True, retrieval_mode="mmr"):
    """
    Tạo chatbot với Conversational Retrieval chain - sử dụng Claude + Memory + Advanced Retrieval
    
    Args:
        vector_store: Vector store (FAISS hoặc Pinecone)
        prompt_template: Template cho prompt
        use_memory: True = Nhớ lịch sử chat, False = Mỗi câu độc lập
        use_advanced_retrieval: True = Dùng re-ranking/hybrid search
        retrieval_mode: "mmr" (default), "rerank", "hybrid", "similarity"
    
    Returns:
        qa_chain: ConversationalRetrievalChain với memory + advanced retrieval
    """
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not anthropic_api_key:
        print("Không tìm thấy ANTHROPIC_API_KEY!")
        print("Vui lòng thêm API key vào file .env")
        print("Lấy API key tại: https://console.anthropic.com/")
        return None
    
    # Tạo LLM với Claude
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.3,
        api_key=anthropic_api_key,
        max_tokens=2000
    )
    
    # Chọn retrieval strategy
    if retrieval_mode == "mmr":
        # MMR (Maximum Marginal Relevance): Đa dạng hóa, tránh duplicate
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 12,  # Tăng từ 8 lên 12 để có nhiều context hơn
                "fetch_k": 30,  # Fetch 30, chọn 12 tốt nhất
                "lambda_mult": 0.5  # Giảm từ 0.7 xuống 0.5 = ưu tiên relevance hơn diversity
            }
        )
        print("Retrieval: MMR (k=12, fetch_k=30, lambda=0.5 - relevance-focused)")
    elif retrieval_mode == "rerank" and use_advanced_retrieval and ADVANCED_RETRIEVAL_AVAILABLE:
        # Re-ranking: Fetch nhiều chunks, LLM đánh giá và xếp hạng lại
        base_retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 20}  # Fetch 20 chunks để re-rank
        )
        retriever = create_reranking_retriever(base_retriever, anthropic_api_key)
        print("Retrieval: Re-ranking với Claude (20 -> 6 chunks)")
    elif retrieval_mode == "hybrid" and use_advanced_retrieval and ADVANCED_RETRIEVAL_AVAILABLE:
        # Hybrid: Vector search + BM25 keyword search
        # Cần truyền documents để tạo BM25 index
        print("Hybrid search cần documents list - fallback sang MMR")
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 8, "fetch_k": 20, "lambda_mult": 0.7}
        )
    else:
        # Default: Similarity search
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 8}
        )
        print("Retrieval: Similarity Search")
    
    if use_memory:
        # Tạo memory để nhớ lịch sử hội thoại
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
            max_token_limit=2000  # Giới hạn 2000 tokens cho history
        )
        
        # Tạo Conversational chain với memory
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=False,
            combine_docs_chain_kwargs={
                "prompt": PromptTemplate(
                    template=prompt_template,
                    input_variables=["context", "question"]
                )
            }
        )
        print("Chatbot đã sẵn sàng (với Conversation Memory)!")
    else:
        # Tạo chain không có memory (như cũ)
        from langchain.chains import RetrievalQA
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template=prompt_template,
                    input_variables=["context", "question"]
                )
            }
        )
        print("Chatbot đã sẵn sàng (không có memory)!")
    
    return qa_chain


def ask_question(qa_chain, question):
    """
    Đặt câu hỏi cho chatbot (hỗ trợ cả memory và non-memory chains)
    
    Args:
        qa_chain: ConversationalRetrievalChain hoặc RetrievalQA chain
        question: Câu hỏi
    
    Returns:
        response: Câu trả lời và source documents
    """
    try:
        # ConversationalRetrievalChain dùng key "question"
        # RetrievalQA dùng key "query"
        if hasattr(qa_chain, 'memory'):
            # Có memory → ConversationalRetrievalChain
            result = qa_chain.invoke({"question": question})
            return {
                'answer': result['answer'],
                'sources': [doc.metadata for doc in result['source_documents']]
            }
        else:
            # Không memory → RetrievalQA
            result = qa_chain.invoke({"query": question})
            return {
                'answer': result['result'],
                'sources': [doc.metadata for doc in result['source_documents']]
            }
    except Exception as e:
        return {
            'answer': f"Xin lỗi, có lỗi xảy ra: {str(e)}",
            'sources': []
        }
