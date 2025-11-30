#!/bin/bash

# Script tự động setup Git và push lên GitHub

echo "🚀 Setup Git Repository và Push lên GitHub"
echo "=========================================="

# Kiểm tra xem đã init git chưa
if [ ! -d ".git" ]; then
    echo "📦 Khởi tạo Git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git đã được khởi tạo"
fi

# Add all files (trừ những gì trong .gitignore)
echo ""
echo "📝 Adding files to staging..."
git add .

# Show what will be committed
echo ""
echo "📋 Files sẽ được commit:"
git status --short

# Commit
echo ""
read -p "💬 Nhập commit message (mặc định: 'Initial commit - RAG Chatbot'): " commit_msg
commit_msg=${commit_msg:-"Initial commit - RAG Chatbot Vật Lý 12"}

git commit -m "$commit_msg"
echo "✅ Committed"

# Add remote (nếu chưa có)
echo ""
echo "🔗 Cấu hình GitHub remote..."
read -p "📍 Nhập GitHub repository URL (vd: https://github.com/username/chatbot.git): " repo_url

if [ -z "$repo_url" ]; then
    echo "❌ Không có URL, bỏ qua bước này"
else
    # Kiểm tra xem remote origin đã tồn tại chưa
    if git remote | grep -q "^origin$"; then
        echo "⚠️  Remote 'origin' đã tồn tại, updating..."
        git remote set-url origin "$repo_url"
    else
        git remote add origin "$repo_url"
    fi
    echo "✅ Remote configured: $repo_url"
    
    # Push
    echo ""
    echo "📤 Pushing to GitHub..."
    read -p "🌿 Branch name (mặc định: main): " branch
    branch=${branch:-main}
    
    # Đổi tên branch nếu đang là master
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$branch" ]; then
        git branch -M "$branch"
    fi
    
    git push -u origin "$branch"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ ================================"
        echo "✅ Push thành công!"
        echo "✅ ================================"
        echo ""
        echo "🌐 Repository: $repo_url"
        echo "🌿 Branch: $branch"
        echo ""
        echo "📝 Bước tiếp theo:"
        echo "   1. Thêm tài liệu PDF vào thư mục data/"
        echo "   2. Tạo file .env từ .env.example"
        echo "   3. Chạy: python upload_to_pinecone.py"
        echo "   4. Chạy: python app.py"
    else
        echo "❌ Push thất bại. Kiểm tra lại:"
        echo "   - Đã tạo repository trên GitHub chưa?"
        echo "   - URL có đúng không?"
        echo "   - Đã authenticate với GitHub chưa? (git config user.name/email)"
    fi
fi

echo ""
echo "🎉 Hoàn tất!"
