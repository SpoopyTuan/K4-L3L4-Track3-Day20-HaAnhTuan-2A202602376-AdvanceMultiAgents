# Pseudo-code 02 - `src/lab/subagents.py`

**Mục tiêu.** Định nghĩa 2 đến 3 tác tử con (subagent) để tác tử chính giao việc qua công cụ `task`.

**Kiểm tra.** `pytest tests/test_02_agent.py`.

`build_agent` tự nối `PATHS_NOTE` (quy ước đường dẫn tương đối) vào `system_prompt` của mỗi subagent, vì subagent không nhận `BASE_PROMPT`. Không cần tự viết lại quy ước này trong `system_prompt`.

`SUBAGENTS_NOTE` (có sẵn trong `agent.py`) khuyến khích tác tử chính giao việc, nhưng tác tử chính vẫn tự quyết định. Trong thực tế thí nghiệm, có trường hợp subagent tự định nghĩa **không được gọi lần nào**. Đó là một kết quả hợp lệ cần ghi vào báo cáo (cột `subagent_calls` trong `run.json`).

---

## Định dạng

Mỗi subagent là một `dict`:

```python
{
    "name": "explorer",                     # bắt buộc, duy nhất
    "description": "Dùng khi ...",          # bắt buộc; tác tử chính đọc mô tả này để quyết định có giao việc hay không
    "system_prompt": "Bạn là ...",          # bắt buộc; chỉ dẫn cho subagent
    # tùy chọn: "tools": [...], "model": "...", "skills": [...], "mode": "isolated" | "fork"
}
```

```text
HÀM get_subagents():
    TRẢ VỀ danh sách gồm các dict trên, ví dụ ba vai trò:
        explorer     - đọc README, docstring, mẫu dữ liệu; báo cáo sự thật; không sửa gì
        implementer  - thực hiện thay đổi, chạy test hoặc script, báo cáo kết quả
        reviewer     - kiểm tra độc lập kết quả theo đề bài và các trường hợp biên; không sửa
```

## Nguyên tắc viết

1. **`description` là chỉ dẫn hành động.** Mô tả rõ *khi nào* nên gọi, không chỉ mô tả vai trò chung chung.
2. **Ngữ cảnh được cô lập (context isolation).** Mỗi lần gọi tạo một phiên bản subagent mới, chỉ nhìn thấy nội dung prompt mà tác tử chính gửi, và trả về **một báo cáo cuối**. Tác tử chính phải truyền đủ thông tin trong prompt.
3. **Chi phí.** Mỗi subagent là thêm các lần gọi mô hình. Đa tác tử (multi-agent) thường tốn nhiều token hơn đáng kể so với một tác tử; bài báo của Anthropic về hệ thống nghiên cứu đa tác tử ghi nhận mức khoảng 15 lần so với hội thoại thường. Hãy ghi lại số token để so sánh ở Phần 5.
4. **Subagent tự định nghĩa không thừa kế skill của tác tử chính.** Chỉ subagent `general-purpose` mặc định được thừa kế. Muốn dùng skill trong subagent tự định nghĩa, thêm khóa `"skills": ["/skills/"]` (nội dung mở rộng, tùy chọn).
5. **Không nên dùng subagent** cho tác vụ một bước đơn giản hoặc khi cần giữ toàn bộ ngữ cảnh trung gian.
