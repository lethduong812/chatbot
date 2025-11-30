"""
Script đánh giá chất lượng chatbot RAG với bộ câu hỏi chuẩn
"""

from src.helper import create_chatbot, create_embeddings
from anthropic import Anthropic
import json
from datetime import datetime
import os

# Bộ câu hỏi test theo từng loại
TEST_CASES = [
    # === LOẠI 1: Kiến thức cơ bản (Fact Recall) ===
    {
        "id": 1,
        "question": "Tốc độ ánh sáng trong chân không là bao nhiêu?",
        "expected_keywords": ["3×10^8", "m/s", "299792458"],
        "category": "fact_recall",
        "difficulty": "easy"
    },
    {
        "id": 2,
        "question": "Sóng điện từ là gì?",
        "expected_keywords": ["sóng ngang", "điện trường", "từ trường", "vuông góc"],
        "category": "fact_recall",
        "difficulty": "easy"
    },
    {
        "id": 3,
        "question": "Định luật bảo toàn năng lượng là gì?",
        "expected_keywords": ["năng lượng", "không đổi", "chuyển hóa", "hệ cô lập"],
        "category": "fact_recall",
        "difficulty": "easy"
    },
    {
        "id": 4,
        "question": "Sóng cơ học cần môi trường truyền không?",
        "expected_keywords": ["cần", "môi trường", "rắn lỏng khí"],
        "category": "fact_recall",
        "difficulty": "easy"
    },
    {
        "id": 5,
        "question": "Hiện tượng giao thoa sóng là gì?",
        "expected_keywords": ["hai nguồn", "kết hợp", "tăng cường", "triệt tiêu"],
        "category": "fact_recall",
        "difficulty": "medium"
    },
    
    # === LOẠI 2: Công thức và tính toán (Formula & Calculation) ===
    {
        "id": 6,
        "question": "Viết công thức tính bước sóng lambda",
        "expected_keywords": ["λ", "v/f", "tốc độ", "tần số"],
        "category": "formula",
        "difficulty": "easy"
    },
    {
        "id": 7,
        "question": "Công thức liên hệ giữa tần số và chu kì là gì?",
        "expected_keywords": ["f = 1/T", "T = 1/f"],
        "category": "formula",
        "difficulty": "easy"
    },
    {
        "id": 8,
        "question": "Viết công thức năng lượng photon",
        "expected_keywords": ["E = hf", "h", "Planck", "6.626"],
        "category": "formula",
        "difficulty": "medium"
    },
    {
        "id": 9,
        "question": "Công thức tính cường độ điện trường E là gì?",
        "expected_keywords": ["E = F/q", "lực", "điện tích"],
        "category": "formula",
        "difficulty": "easy"
    },
    {
        "id": 10,
        "question": "Liệt kê các công thức quan trọng trong bài sóng cơ",
        "expected_keywords": ["v = λf", "T = 1/f", "phương trình sóng"],
        "category": "formula",
        "difficulty": "medium"
    },
    
    # === LOẠI 3: So sánh (Comparison) ===
    {
        "id": 11,
        "question": "So sánh sóng dọc và sóng ngang",
        "expected_keywords": ["dọc", "ngang", "phương dao động", "phương truyền"],
        "category": "comparison",
        "difficulty": "medium"
    },
    {
        "id": 12,
        "question": "Phân biệt sóng cơ và sóng điện từ",
        "expected_keywords": ["môi trường", "chân không", "cơ học", "điện từ"],
        "category": "comparison",
        "difficulty": "medium"
    },
    {
        "id": 13,
        "question": "Khác nhau giữa hiện tượng giao thoa và nhiễu xạ",
        "expected_keywords": ["giao thoa", "nhiễu xạ", "hai nguồn", "vật cản"],
        "category": "comparison",
        "difficulty": "hard"
    },
    {
        "id": 14,
        "question": "So sánh ánh sáng đơn sắc và ánh sáng trắng",
        "expected_keywords": ["đơn sắc", "trắng", "tần số", "phổ"],
        "category": "comparison",
        "difficulty": "medium"
    },
    
    # === LOẠI 4: Giải thích (Explanation) ===
    {
        "id": 15,
        "question": "Giải thích hiện tượng phân xạ sóng",
        "expected_keywords": ["phản xạ", "khúc xạ", "bề mặt", "góc"],
        "category": "explanation",
        "difficulty": "medium"
    },
    {
        "id": 16,
        "question": "Tại sao sóng âm không truyền được trong chân không?",
        "expected_keywords": ["sóng cơ", "môi trường", "chân không", "dao động"],
        "category": "explanation",
        "difficulty": "medium"
    },
    {
        "id": 17,
        "question": "Giải thích tại sao ánh sáng có tính chất sóng và hạt",
        "expected_keywords": ["lưỡng tính", "sóng", "hạt", "photon", "giao thoa"],
        "category": "explanation",
        "difficulty": "hard"
    },
    {
        "id": 18,
        "question": "Vì sao điện trường và từ trường vuông góc với nhau trong sóng điện từ?",
        "expected_keywords": ["Maxwell", "vuông góc", "dao động", "truyền"],
        "category": "explanation",
        "difficulty": "hard"
    },
    
    # === LOẠI 5: Ứng dụng thực tế (Application) ===
    {
        "id": 19,
        "question": "Ứng dụng của sóng điện từ trong đời sống",
        "expected_keywords": ["radio", "wifi", "y tế", "truyền thông"],
        "category": "application",
        "difficulty": "medium"
    },
    {
        "id": 20,
        "question": "Hiện tượng giao thoa ánh sáng được ứng dụng ở đâu?",
        "expected_keywords": ["màng phản quang", "kiểm tra", "đo lường"],
        "category": "application",
        "difficulty": "medium"
    },
    {
        "id": 21,
        "question": "Tại sao radar dùng sóng điện từ?",
        "expected_keywords": ["phản xạ", "tốc độ ánh sáng", "khoảng cách"],
        "category": "application",
        "difficulty": "medium"
    },
    
    # === LOẠI 6: Câu hỏi phức tạp (Complex/Multi-step) ===
    {
        "id": 22,
        "question": "Mô tả quá trình truyền sóng âm từ nguồn đến tai người",
        "expected_keywords": ["dao động", "môi trường", "màng nhĩ", "truyền"],
        "category": "complex",
        "difficulty": "hard"
    },
    {
        "id": 23,
        "question": "Liệt kê và giải thích các tính chất của sóng điện từ",
        "expected_keywords": ["sóng ngang", "chân không", "năng lượng", "phổ"],
        "category": "complex",
        "difficulty": "hard"
    },
    {
        "id": 24,
        "question": "So sánh và phân tích sự khác nhau giữa các loại sóng trong chương 1",
        "expected_keywords": ["sóng cơ", "sóng điện từ", "môi trường", "tốc độ"],
        "category": "complex",
        "difficulty": "hard"
    },
    
    # === LOẠI 7: Câu hỏi biên (Edge Cases) ===
    {
        "id": 25,
        "question": "Con số Pi bằng bao nhiêu?",
        "expected_answer": "Xin lỗi, tôi chỉ trả lời các câu hỏi về Vật Lí 12",
        "category": "out_of_scope",
        "difficulty": "easy"
    },
    {
        "id": 26,
        "question": "Cách nấu phở ngon",
        "expected_answer": "Xin lỗi, tôi chỉ trả lời các câu hỏi về Vật Lí 12",
        "category": "out_of_scope",
        "difficulty": "easy"
    },
    {
        "id": 27,
        "question": "Có phải tất cả các sóng đều có tần số không?",
        "expected_keywords": ["có", "tần số", "dao động"],
        "category": "tricky",
        "difficulty": "medium"
    },
    {
        "id": 28,
        "question": "Sóng nào nhanh nhất?",
        "expected_keywords": ["ánh sáng", "sóng điện từ", "3×10^8"],
        "category": "tricky",
        "difficulty": "easy"
    },
    
    # === LOẠI 8: Câu hỏi về nguồn và chương cụ thể ===
    {
        "id": 29,
        "question": "Chương 1 nói về gì?",
        "expected_keywords": ["dao động", "sóng", "cơ học", "điện từ"],
        "category": "meta",
        "difficulty": "easy"
    },
    {
        "id": 30,
        "question": "Có bao nhiêu bài trong chương 1?",
        "expected_keywords": ["bài", "chương 1"],
        "category": "meta",
        "difficulty": "easy"
    },
]


def evaluate_answer_simple(question, bot_answer, expected_keywords):
    """
    Đánh giá đơn giản bằng keyword matching (KHÔNG TỐN PHÍ)
    """
    if not expected_keywords:
        return {
            "accuracy": 3,
            "completeness": 3,
            "clarity": 3,
            "relevance": 3,
            "overall": 3,
            "feedback": "Không có keywords để đánh giá",
            "missing_keywords": []
        }
    
    bot_answer_lower = bot_answer.lower()
    
    # Đếm số keywords xuất hiện
    matched = [kw for kw in expected_keywords if kw.lower() in bot_answer_lower]
    missing = [kw for kw in expected_keywords if kw.lower() not in bot_answer_lower]
    
    match_ratio = len(matched) / len(expected_keywords)
    
    # Check xem có từ chối không
    rejection_phrases = ["xin lỗi", "không tìm thấy", "không có thông tin"]
    is_rejection = any(phrase in bot_answer_lower for phrase in rejection_phrases)
    
    # Tính điểm
    if is_rejection and match_ratio < 0.2:
        # Bot từ chối và không có keywords → Rất tệ
        score = 1
        feedback = f"Bot từ chối trả lời. Missing: {', '.join(missing)}"
    elif match_ratio >= 0.8:
        score = 5
        feedback = f"Xuất sắc! Có {len(matched)}/{len(expected_keywords)} keywords"
    elif match_ratio >= 0.6:
        score = 4
        feedback = f"Tốt. Có {len(matched)}/{len(expected_keywords)} keywords. Thiếu: {', '.join(missing[:2])}"
    elif match_ratio >= 0.4:
        score = 3
        feedback = f"Trung bình. Có {len(matched)}/{len(expected_keywords)} keywords. Thiếu: {', '.join(missing[:3])}"
    elif match_ratio >= 0.2:
        score = 2
        feedback = f"Yếu. Chỉ có {len(matched)}/{len(expected_keywords)} keywords"
    else:
        score = 1
        feedback = f"Rất tệ. Thiếu hầu hết keywords: {', '.join(missing[:4])}"
    
    return {
        "accuracy": score,
        "completeness": score,
        "clarity": score,
        "relevance": score,
        "overall": score,
        "feedback": feedback,
        "missing_keywords": missing
    }


def evaluate_answer_with_llm(question, bot_answer, expected_keywords):
    """
    Dùng Claude làm judge để đánh giá câu trả lời (TỐN $$$)
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = f"""Bạn là giáo viên Vật Lí, đánh giá câu trả lời của chatbot học sinh.

Câu hỏi: {question}
Từ khóa cần có: {', '.join(expected_keywords) if expected_keywords else 'N/A'}
Câu trả lời của bot: {bot_answer}

Đánh giá theo thang điểm 5:
1. **Độ chính xác (Accuracy)**: Thông tin có đúng không? (1-5)
2. **Độ đầy đủ (Completeness)**: Có đủ từ khóa quan trọng không? (1-5)
3. **Độ rõ ràng (Clarity)**: Giải thích có dễ hiểu, có cấu trúc không? (1-5)
4. **Độ liên quan (Relevance)**: Có trả lời đúng câu hỏi không? (1-5)

Trả về JSON:
{{
    "accuracy": 1-5,
    "completeness": 1-5,
    "clarity": 1-5,
    "relevance": 1-5,
    "overall": 1-5,
    "feedback": "Nhận xét ngắn gọn",
    "missing_keywords": ["từ khóa thiếu nếu có"]
}}

CHỈ TRẢ VỀ JSON, KHÔNG THÊM TEXT NÀO KHÁC."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        # Thử extract JSON từ response (có thể có text thừa)
        try:
            # Tìm dấu { và } đầu tiên
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start != -1 and end != -1:
                json_str = response_text[start:end+1]
                result = json.loads(json_str)
                return result
            else:
                raise ValueError("Không tìm thấy JSON trong response")
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: parse thủ công hoặc dùng điểm mặc định
            print(f"⚠️  Không parse được JSON: {e}")
            print(f"   Response: {response_text[:200]}...")
            
            # Đánh giá đơn giản dựa trên keywords
            text_lower = bot_answer.lower()
            matched = sum(1 for kw in expected_keywords if kw.lower() in text_lower)
            score = min(5, max(1, int(matched / len(expected_keywords) * 5))) if expected_keywords else 3
            
            return {
                "accuracy": score,
                "completeness": score,
                "clarity": score,
                "relevance": score,
                "overall": score,
                "feedback": f"Auto-scored: {matched}/{len(expected_keywords)} keywords matched",
                "missing_keywords": [kw for kw in expected_keywords if kw.lower() not in text_lower]
            }
            
    except Exception as e:
        print(f"❌ Lỗi khi gọi API: {e}")
        return {
            "accuracy": 0,
            "completeness": 0,
            "clarity": 0,
            "relevance": 0,
            "overall": 0,
            "feedback": f"API Error: {str(e)}",
            "missing_keywords": []
        }


def run_evaluation(use_llm_judge=False):
    """
    Chạy toàn bộ test cases
    
    Args:
        use_llm_judge: True = Dùng Claude judge (tốn $$), False = Keyword matching (free)
    """
    print("🚀 Bắt đầu đánh giá chatbot...")
    print(f"📊 Phương pháp: {'LLM Judge ($$)' if use_llm_judge else 'Keyword Matching (FREE)'}")
    print("=" * 80)
    
    # Khởi tạo chatbot
    print("\n📚 Đang tải embeddings...")
    embeddings = create_embeddings()
    
    print("🔗 Đang kết nối với Pinecone...")
    from langchain_pinecone import PineconeVectorStore
    from src.prompt import prompt_template
    
    vector_store = PineconeVectorStore(
        index_name="studychatbot",
        embedding=embeddings
    )
    
    print("🤖 Đang tạo chatbot với MMR...")
    qa_chain = create_chatbot(
        vector_store=vector_store,
        prompt_template=prompt_template,
        use_memory=True,
        retrieval_mode="mmr"
    )
    
    results = []
    total_score = 0
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Câu hỏi: {test['question']}")
        print(f"   Loại: {test['category']} | Độ khó: {test['difficulty']}")
        
        try:
            # Lấy câu trả lời từ chatbot
            response = qa_chain.invoke({"question": test["question"]})
            bot_answer = response["answer"]
            
            print(f"   ✅ Bot trả lời: {bot_answer[:100]}..." if len(bot_answer) > 100 else f"   ✅ Bot trả lời: {bot_answer}")
            
            # Đánh giá
            if "expected_keywords" in test:
                if use_llm_judge:
                    evaluation = evaluate_answer_with_llm(
                        test["question"],
                        bot_answer,
                        test["expected_keywords"]
                    )
                else:
                    evaluation = evaluate_answer_simple(
                        test["question"],
                        bot_answer,
                        test["expected_keywords"]
                    )
            else:
                # Câu out_of_scope chỉ check xem có từ chối không
                evaluation = {
                    "accuracy": 5 if "xin lỗi" in bot_answer.lower() or "không thể" in bot_answer.lower() else 1,
                    "completeness": 5,
                    "clarity": 5,
                    "relevance": 5,
                    "overall": 5 if "xin lỗi" in bot_answer.lower() else 1,
                    "feedback": "Đúng - đã từ chối câu hỏi ngoài phạm vi" if "xin lỗi" in bot_answer.lower() else "Sai - không từ chối câu hỏi ngoài phạm vi",
                    "missing_keywords": []
                }
            
            # Lưu kết quả
            result = {
                **test,
                "bot_answer": bot_answer,
                "evaluation": evaluation,
                "sources": [doc.metadata.get("source", "unknown") for doc in response.get("source_documents", [])]
            }
            results.append(result)
            
            total_score += evaluation["overall"]
            
            print(f"   📊 Điểm tổng: {evaluation['overall']}/5")
            print(f"   💬 Feedback: {evaluation['feedback']}")
            
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            results.append({
                **test,
                "bot_answer": f"ERROR: {str(e)}",
                "evaluation": {
                    "accuracy": 0,
                    "completeness": 0,
                    "clarity": 0,
                    "relevance": 0,
                    "overall": 0,
                    "feedback": f"Lỗi hệ thống: {str(e)}",
                    "missing_keywords": []
                },
                "sources": []
            })
    
    # Tính toán thống kê
    print("\n" + "=" * 80)
    print("📈 KẾT QUẢ ĐÁNH GIÁ")
    print("=" * 80)
    
    avg_score = total_score / len(TEST_CASES)
    print(f"\n🎯 Điểm trung bình: {avg_score:.2f}/5.00")
    
    # Thống kê theo category
    categories = {}
    for result in results:
        cat = result["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "count": 0}
        categories[cat]["total"] += result["evaluation"]["overall"]
        categories[cat]["count"] += 1
    
    print("\n📊 Điểm theo loại câu hỏi:")
    for cat, stats in categories.items():
        avg = stats["total"] / stats["count"]
        print(f"   - {cat:20s}: {avg:.2f}/5 ({stats['count']} câu)")
    
    # Thống kê theo độ khó
    difficulties = {}
    for result in results:
        diff = result["difficulty"]
        if diff not in difficulties:
            difficulties[diff] = {"total": 0, "count": 0}
        difficulties[diff]["total"] += result["evaluation"]["overall"]
        difficulties[diff]["count"] += 1
    
    print("\n📊 Điểm theo độ khó:")
    for diff, stats in difficulties.items():
        avg = stats["total"] / stats["count"]
        print(f"   - {diff:10s}: {avg:.2f}/5 ({stats['count']} câu)")
    
    # Top 5 câu trả lời tốt nhất
    print("\n🏆 TOP 5 CÂU TRẢ LỜI TỐT NHẤT:")
    sorted_results = sorted(results, key=lambda x: x["evaluation"]["overall"], reverse=True)
    for i, result in enumerate(sorted_results[:5], 1):
        print(f"{i}. [{result['evaluation']['overall']}/5] {result['question']}")
    
    # Top 5 câu trả lời cần cải thiện
    print("\n⚠️  TOP 5 CÂU CẦN CẢI THIỆN:")
    for i, result in enumerate(sorted_results[-5:], 1):
        print(f"{i}. [{result['evaluation']['overall']}/5] {result['question']}")
        print(f"   💡 {result['evaluation']['feedback']}")
    
    # Lưu kết quả ra file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"evaluation_results_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "total_questions": len(TEST_CASES),
            "average_score": avg_score,
            "category_scores": {cat: stats["total"]/stats["count"] for cat, stats in categories.items()},
            "difficulty_scores": {diff: stats["total"]/stats["count"] for diff, stats in difficulties.items()},
            "detailed_results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Kết quả chi tiết đã lưu vào: {output_file}")
    print("\n✅ Hoàn thành đánh giá!")


if __name__ == "__main__":
    import sys
    
    # Mặc định: Keyword matching (FREE)
    # Chạy với LLM judge: python evaluate.py --llm
    use_llm = "--llm" in sys.argv
    
    if use_llm:
        print("⚠️  WARNING: Sử dụng LLM judge sẽ tốn ~$4 cho 30 câu!")
        confirm = input("Tiếp tục? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Đã hủy.")
            exit(0)
    
    run_evaluation(use_llm_judge=use_llm)
