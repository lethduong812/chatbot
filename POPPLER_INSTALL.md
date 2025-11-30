# Hướng dẫn cài đặt Poppler cho pdf2image trên Windows

## Poppler là gì?
Poppler là thư viện cần thiết để pdf2image chuyển đổi PDF thành hình ảnh.

## Cách cài đặt:

### Cách 1: Tải trực tiếp (Khuyến nghị)

1. Tải Poppler cho Windows từ: https://github.com/oschwartz10612/poppler-windows/releases/
2. Tải file `Release-XX.XX.X-0.zip` (phiên bản mới nhất)
3. Giải nén vào thư mục, ví dụ: `C:\Program Files\poppler`
4. Thêm `C:\Program Files\poppler\Library\bin` vào PATH:
   - Mở Settings > System > About > Advanced system settings
   - Click "Environment Variables"
   - Trong "System variables", chọn "Path" và click "Edit"
   - Click "New" và thêm: `C:\Program Files\poppler\Library\bin`
   - Click OK

### Cách 2: Sử dụng trong code (không cần PATH)

```python
# Trong helper.py, thay đổi hàm extract_images_from_pdf:
images = convert_from_path(
    file_path, 
    first_page=page_num + 1, 
    last_page=page_num + 1,
    dpi=150,
    poppler_path=r"C:\Program Files\poppler\Library\bin"  # Đường dẫn poppler
)
```

## Test xem đã cài đúng chưa:

```bash
# Trong terminal
pdfinfo -v
```

Nếu hiện version của Poppler là OK!

## Lưu ý:
- Khởi động lại terminal sau khi thêm PATH
- Nếu không muốn cài Poppler, đặt `extract_images=False` khi gọi `load_all_pdfs()`
