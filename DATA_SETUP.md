# Hướng dẫn chuẩn bị dữ liệu

Repository này **KHÔNG bao gồm** tài liệu PDF gốc (do bản quyền và kích thước file lớn).

## Cách setup dữ liệu

### Option 1: Sử dụng tài liệu của riêng bạn

1. Tạo thư mục `data/`:
```bash
mkdir data
```

2. Thêm các file PDF vào `data/`:
```
data/
├── document1.pdf
├── document2.pdf
├── document3.pdf
└── ...
```

3. Upload lên Pinecone:
```bash
python upload_to_pinecone.py
```

### Option 2: Download tài liệu mẫu

Nếu bạn cần tài liệu Vật Lý 12, có thể:
- Download từ website giáo dục
- Liên hệ tác giả project để xin file (nếu có)
- Sử dụng sách giáo khoa điện tử của Bộ GD&ĐT
```

## Thông tin về dữ liệu

- **Định dạng**: PDF (text + hình ảnh)
- File PDF phải có OCR (có thể extract text)
- Nếu PDF là scan ảnh → Cần OCR trước
- Image extraction tốn phí Claude Vision API (~$0.012/image)
- Mặc định: `extract_images=False` để tiết kiệm chi phí

## 🔧 Troubleshooting

**Lỗi: "data/ directory not found"**
```bash
mkdir data
# Thêm PDF vào data/
```

**Lỗi: "No PDF files found"**
- Kiểm tra files có đuôi `.pdf` không
- File có đặt đúng trong `data/` không

**Lỗi: "Cannot extract text from PDF"**
- PDF có thể là scan ảnh, cần OCR
- Thử tool: https://www.ilovepdf.com/ocr-pdf
