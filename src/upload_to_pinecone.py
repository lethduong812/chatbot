"""
Script để upload dữ liệu từ PDF lên Pinecone
Chạy script này để đẩy toàn bộ PDF lên Pinecone index
"""

import os
import sys
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.helper import (
    load_all_pdfs,
    split_text_into_chunks,
    create_embeddings
)

# Load environment variables
load_dotenv()

INDEX_NAME = "studychatbot"

def delete_and_create_index(use_phobert=True):
    """Xóa index cũ và tạo mới với dimension phù hợp"""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ Không tìm thấy PINECONE_API_KEY trong file .env!")
        return False
    
    pc = Pinecone(api_key=api_key)
    
    # List all indexes
    existing_indexes = [index.name for index in pc.list_indexes()]
    
    print(f"📋 Các index hiện có: {existing_indexes}")
    
    # Delete if exists
    if INDEX_NAME in existing_indexes:
        print(f"🗑️  Đang xóa index cũ: {INDEX_NAME}")
        pc.delete_index(INDEX_NAME)
        print("✅ Đã xóa index cũ!")
        
        import time
        print("⏳ Đợi 10 giây...")
        time.sleep(10)
    
    # Determine dimension based on model
    dimension = 768 if use_phobert else 384
    model_name = "PhoBERT (768D)" if use_phobert else "Multilingual MiniLM (384D)"
    
    # Create new index
    print(f"🆕 Đang tạo index mới: {INDEX_NAME}")
    print(f"📐 Dimension: {dimension} ({model_name})")
    pc.create_index(
        name=INDEX_NAME,
        dimension=dimension,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )
    
    print("✅ Đã tạo index mới!")
    print("⏳ Đợi index sẵn sàng (20 giây)...")
    import time
    time.sleep(20)
    
    return True

def upload_data_to_pinecone(use_phobert=True):
    """Upload dữ liệu từ PDF lên Pinecone"""
    print("\n" + "=" * 60)
    print("🚀 BẮT ĐẦU UPLOAD DỮ LIỆU LÊN PINECONE")
    print("=" * 60)
    
    model_name = "🇻🇳 PhoBERT" if use_phobert else "🌍 Multilingual MiniLM"
    print(f"📊 Embedding Model: {model_name}")
    
    # Step 1: Delete and create index
    if not delete_and_create_index(use_phobert):
        return
    
    # Step 2: Load PDFs
    print("\n📚 BƯỚC 1: Đọc file PDF từ thư mục data/")
    documents = load_all_pdfs("data", extract_images=False)  # Tắt vision để tiết kiệm
    
    if not documents:
        print("❌ Không tìm thấy file PDF nào!")
        return
    
    print(f"✅ Đã đọc {len(documents)} file PDF")
    
    # Step 3: Split into chunks
    print("\n✂️  BƯỚC 2: Chia text thành chunks")
    chunks = split_text_into_chunks(documents, chunk_size=1000, chunk_overlap=200)
    print(f"✅ Đã tạo {len(chunks)} chunks")
    
    # Step 4: Create embeddings
    print("\n🧠 BƯỚC 3: Tạo embeddings")
    embeddings = create_embeddings(use_phobert=use_phobert)
    print("✅ Embeddings đã sẵn sàng")
    
    # Step 5: Upload to Pinecone
    print("\n☁️  BƯỚC 4: Upload lên Pinecone (có thể mất vài phút...)")
    
    from langchain_pinecone import PineconeVectorStore
    
    texts = [chunk['text'] for chunk in chunks]
    metadatas = [{'source': chunk['source'], 'chunk_id': chunk['chunk_id']} 
                 for chunk in chunks]
    
    print(f"📤 Đang upload {len(texts)} chunks lên Pinecone...")
    
    try:
        vector_store = PineconeVectorStore.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            index_name=INDEX_NAME,
            namespace=""  # default namespace
        )
        
        print("\n" + "=" * 60)
        print("✅ ✅ ✅ HOÀN THÀNH! ✅ ✅ ✅")
        print("=" * 60)
        print(f"📊 Đã upload {len(texts)} chunks vào index '{INDEX_NAME}'")
        print("🎉 Bây giờ bạn có thể chạy app và hỏi câu hỏi!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ LỖI khi upload: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n⚠️  CẢNH BÁO: Script này sẽ XÓA toàn bộ dữ liệu cũ trong Pinecone!")
    print(f"⚠️  Index '{INDEX_NAME}' sẽ bị xóa và tạo lại từ đầu.")
    
    print("\n📊 Chọn Embedding Model:")
    print("  1. PhoBERT (768D) - Tối ưu tiếng Việt, chính xác cao ✅")
    print("  2. Multilingual MiniLM (384D) - Nhanh hơn, đa ngôn ngữ")
    
    model_choice = input("\n❓ Chọn model (1 hoặc 2, mặc định 1): ").strip()
    use_phobert = True if model_choice != '2' else False
    
    response = input("\n❓ Bạn có chắc chắn muốn tiếp tục? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        upload_data_to_pinecone(use_phobert=use_phobert)
    else:
        print("❌ Đã hủy!")
