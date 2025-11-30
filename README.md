# Chatbot Học Tập Vật Lý - RAG với Claude AI

> Chatbot AI thông minh giúp sinh viên học tập từ tài liệu PDF về Vật Lý, sử dụng công nghệ RAG (Retrieval-Augmented Generation) với Claude 3.5 Sonnet.

## Tính năng chính

- **Đọc và phân tích PDF**: Trích xuất text + hình ảnh (sơ đồ, công thức, đồ thị)
- **Claude 4.5 Sonnet**: LLM mạnh mẽ, trả lời bằng tiếng Việt tự nhiên
- **PhoBERT Embeddings**: Model embedding tối ưu cho tiếng Việt (768D)
- **Pinecone Vector Database**: Lưu trữ và tìm kiếm nhanh trên cloud
- **Claude Vision API**: Hiểu hình ảnh trong PDF (sơ đồ, biểu đồ, công thức)
- **Conversation Memory**: Nhớ lịch sử chat, trả lời câu hỏi follow-up
- **Advanced Retrieval**:
  - **MMR** (Maximum Marginal Relevance): Tránh trùng lặp, đa dạng context
- **Web Interface**: Giao diện đẹp, thân thiện, chuyển đổi retrieval mode dễ dàng

## Tech Stack

| Component | Technology |
|-----------|------------|
| **LLM** | Claude 4.5 Sonnet (Anthropic) |
| **Vision** | Claude Vision API |
| **Embeddings** | PhoBERT (VoVanPhuc/sup-SimCSE-VietNamese-phobert-base) |
| **Vector DB** | Pinecone (cloud) |
| **Framework** | LangChain 0.3.26 |
| **Web Server** | Flask 3.1.1 |
| **PDF Processing** | pypdf, pdf2image, Pillow |
| **Retrieval** | MMR, Hybrid Search (BM25 + Vector) - chưa hoàn thiện |

## Cài đặt

### 1. Clone và setup environment

```bash
# Clone repository
git clone <repo-url>
cd Chatbot

# Tạo virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
# hoặc: .venv\Scripts\activate  # Windows CMD
# hoặc: source .venv/bin/activate  # Linux/Mac

# Cài dependencies
pip install -r requirements.txt
```

### 2. Cấu hình API Keys

Tạo file `.env` từ template:

```bash
cp .env.example .env
```

Chỉnh sửa `.env` và thêm API keys:

```env
# Claude API Key (bắt buộc)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Pinecone API Key (bắt buộc)
PINECONE_API_KEY=pcsk_xxxxx
```

**Lấy API Keys:**
- **Claude**: https://console.anthropic.com/settings/keys
- **Pinecone**: https://app.pinecone.io/ → API Keys (Free tier: 1GB)

### 3. Cài Poppler (Windows - cho pdf2image)

**Bắt buộc nếu muốn xử lý hình ảnh trong PDF!**

```bash
# Download: https://github.com/oschwartz10612/poppler-windows/releases/
# Tải Release-XX.XX.X-0.zip
# Giải nén vào: C:\Program Files\poppler
# Thêm vào PATH: C:\Program Files\poppler\Library\bin
```

Chi tiết xem: `POPPLER_INSTALL.md`

### 4. Thêm file PDF

Đặt file PDF vào thư mục `data/`:

```
data/
├── 1_Phongtoanhiet.pdf
├── 2_Phongtoakhi.pdf
├── 3_Phongtoatutruong.pdf
└── 4_phongtoahatnhan.pdf
```

### 5. Upload dữ liệu lên Pinecone

**Lần đầu tiên hoặc khi thêm PDF mới:**

```bash
python upload_to_pinecone.py
```

Script sẽ:
1. Đọc tất cả PDF trong `data/`
2. Trích xuất text + hình ảnh (3 trang đầu mỗi PDF)
3. Phân tích hình ảnh với Claude Vision API
4. Tạo embeddings với PhoBERT (768D)
5. Upload lên Pinecone index `studychatbot`

**Thời gian:** ~5-10 phút (tùy số lượng PDF và ảnh)

### 6. Chạy ứng dụng

```bash
python app.py
```

Mở trình duyệt: **http://localhost:5000**

## 📝 License

MIT License

## 👨‍💻 Tác giả

**Lê Thái Dương**
- Email: lethduong812@gmail.com

---

**Chúc bạn học tập hiệu quả!**
