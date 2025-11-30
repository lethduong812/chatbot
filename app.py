"""
Flask App - Chatbot học tập với Pinecone Vector Store
"""

from flask import Flask, render_template, request, jsonify
import os
from src.helper import (
    load_all_pdfs,
    split_text_into_chunks,
    create_embeddings,
    create_chatbot,
    ask_question
)
from src.prompt import prompt_template, welcome_message
from langchain_pinecone import PineconeVectorStore

app = Flask(__name__)

# Global variables
qa_chain = None
vector_store = None
embeddings = None
INDEX_NAME = "studychatbot"


def initialize_chatbot():
    """
    Khởi tạo chatbot với Pinecone vector store (MMR only)
    """
    global qa_chain, vector_store, embeddings
    
    print("=" * 50)
    print("Đang khởi tạo chatbot với Pinecone...")
    print("=" * 50)
    
    # Kiểm tra Pinecone API key
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        print("Không tìm thấy PINECONE_API_KEY trong file .env!")
        return False
    
    # Tạo embeddings nếu chưa có
    if embeddings is None:
        embeddings = create_embeddings()
    
    # Kết nối với Pinecone index
    try:
        print(f"Đang kết nối với Pinecone index: {INDEX_NAME}")
        vector_store = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=embeddings
        )
        print("Đã kết nối với Pinecone!")
    except Exception as e:
        print(f"Lỗi kết nối Pinecone: {str(e)}")
        print("Đảm bảo bạn đã chạy upload_to_pinecone.py để tạo index!")
        return False
    
    if vector_store is None:
        print("Không thể tạo vector store!")
        return False
    
    # Create chatbot với MMR (mặc định)
    qa_chain = create_chatbot(vector_store, prompt_template, 
                              use_memory=True, 
                              retrieval_mode="mmr")
    
    if qa_chain is None:
        print("Không thể tạo chatbot - thiếu Claude API key")
        print("Vui lòng thêm ANTHROPIC_API_KEY vào file .env")
        return False
    
    print("=" * 50)
    print("Chatbot đã sẵn sàng!")
    print("=" * 50)
    return True


@app.route('/')
def home():
    """
    Trang chủ
    """
    return render_template('index.html')


@app.route('/api/ask', methods=['POST'])
def ask():
    """
    API endpoint để đặt câu hỏi - Hỗ trợ conversation memory
    """
    global qa_chain
    
    data = request.json
    question = data.get('question', '')
    
    if qa_chain is None:
        return jsonify({
            'success': False,
            'answer': "Chatbot chưa sẵn sàng. Vui lòng thêm API keys vào file .env và khởi động lại.",
            'sources': []
        })
    
    if not question:
        return jsonify({
            'success': False,
            'answer': "Vui lòng nhập câu hỏi!",
            'sources': []
        })
    
    try:
        response = ask_question(qa_chain, question)
        
        return jsonify({
            'success': True,
            'answer': response['answer'],
            'sources': response['sources']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'answer': f"Lỗi: {str(e)}",
            'sources': []
        })


@app.route('/api/rebuild', methods=['POST'])
def rebuild_index():
    """
    API endpoint để rebuild Pinecone index từ PDF
    """
    try:
        print("Đang rebuild Pinecone index...")
        print("Vui lòng chạy: python upload_to_pinecone.py")
        
        return jsonify({
            'success': False,
            'message': "Để rebuild Pinecone, vui lòng chạy: python upload_to_pinecone.py"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Lỗi: {str(e)}"
        })


if __name__ == '__main__':
    # Khởi tạo chatbot khi start app (MMR mặc định)
    initialize_chatbot()
    
    # Chạy Flask app
    print("\nStarting Flask server...")
    print("Mở trình duyệt và truy cập: http://localhost:5000")
    print("Nhấn Ctrl+C để dừng server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
