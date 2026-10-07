# Bảng thuật ngữ (GLOSSARY)

Quy ước: thuật ngữ được dịch sang tiếng Việt kèm bản gốc tiếng Anh trong ngoặc. Một số thuật ngữ giữ nguyên tiếng Anh vì được dùng phổ biến (token, prompt, API, trace, skill trong mã nguồn).

| Tiếng Việt | Tiếng Anh | Giải nghĩa trong lab |
|---|---|---|
| Tác tử | agent | Chương trình dùng mô hình ngôn ngữ để lặp: suy luận, gọi công cụ, quan sát kết quả, cho đến khi hoàn thành. |
| Bộ khung điều khiển | harness | Phần mã bao quanh mô hình: vòng lặp, công cụ, system prompt, quản lý ngữ cảnh, subagent, skill. Deep Agents là một harness. |
| Công cụ | tool | Hàm mà mô hình được phép gọi (đọc tệp, ghi tệp, chạy shell, giao việc cho subagent). |
| Môi trường thực thi | backend | Thành phần cung cấp hệ thống tệp và khả năng chạy lệnh cho các công cụ. |
| Môi trường cách ly | sandbox | Thư mục tạm riêng cho mỗi lần chạy, để tác tử không sửa tệp gốc. |
| Tác tử con | subagent | Tác tử phụ do tác tử chính giao việc qua công cụ `task`; có ngữ cảnh riêng và trả về một báo cáo cuối. |
| Đa tác tử | multi-agent | Hệ thống gồm nhiều tác tử phối hợp (ở đây: tác tử chính và các subagent). |
| Cô lập ngữ cảnh | context isolation | Mỗi subagent chỉ nhìn thấy prompt được giao, không thấy toàn bộ hội thoại của tác tử chính. |
| Kỹ năng | skill | Thư mục có `SKILL.md` mô tả một quy trình; tác tử nạp khi tác vụ phù hợp. |
| Nạp dần | progressive disclosure | Tác tử chỉ thấy tên và mô tả skill lúc đầu, đọc toàn bộ nội dung khi cần. |
| Ngữ cảnh | context | Toàn bộ văn bản mà mô hình nhìn thấy ở mỗi lượt gọi. |
| Tầng ngữ cảnh | context layer | Phần của tác tử có thể cải thiện mà không đổi trọng số mô hình: instruction, skill, bộ nhớ. |
| Tiến hóa (tự cải thiện) | evolution (self-improvement) | Tác tử hoặc hệ thống xung quanh thay đổi cách làm dựa trên kinh nghiệm đã thu thập. |
| Vết thực thi | trace | Bản ghi mọi bước của một lần chạy: lời nói của mô hình, lệnh gọi công cụ, kết quả công cụ. |
| Tuyển chọn skill | skill curation | Quá trình đọc vết thất bại và viết, sửa hoặc bỏ skill. `curator` là chương trình thực hiện. |
| Tác vụ | task | Một bài toán cho tác tử, kèm đề bài, dữ liệu và bộ kiểm tra tự động. |
| Họ tác vụ | task family | Nhóm tác vụ cùng loại kỹ năng (code, data, logs). |
| Tác vụ học | learning task | Tác vụ được dùng để quan sát lỗi và rút skill. Tương đương tập huấn luyện. |
| Tác vụ đánh giá | evaluation task | Tác vụ giữ riêng để đo skill có tổng quát hóa hay không. Tương đương tập kiểm thử. |
| Điều kiện thí nghiệm | condition | Một cấu hình tác tử: `baseline`, `subagents`, `skills-auto`. |
| Đường cơ sở | baseline | Cấu hình mặc định, làm mốc so sánh. |
| Phép kiểm tra | check | Một điều kiện tự động của `check.py`; điểm tác vụ là tỉ lệ check đạt. |
| Chấm điểm từng phần | partial credit | Điểm bằng tỉ lệ check đạt, không chỉ đạt hoặc không đạt. |
| Đóng băng | freeze | Chốt skill, không sửa nữa trước khi chạy tác vụ đánh giá. |
| Quá khớp | overfitting | Skill giúp tác vụ học nhưng không giúp tác vụ mới vì chỉ ghi nhớ chi tiết riêng của tác vụ học. |
| Rò rỉ dữ liệu | data leakage | Thông tin của tập đánh giá lọt vào quá trình học (ví dụ chép đáp án vào skill). |
| Quy ước tổ chức | house rules | Quy tắc của tổ chức "Acme" mà bot đánh giá kiểm tra nhưng đề bài không nêu (đơn vị tiền tệ, khối `meta`, thứ tự sắp xếp, ...). Tri thức loại này chỉ học được từ phản hồi. |
| Bot đánh giá | review bot | Bộ kiểm tra tự động (`check.py`) mô phỏng người rà soát của tổ chức; ở tác vụ học nó trả về nhận xét `detail`. |
| Phản hồi | feedback | Trường `detail` của check thất bại trong `run.json` của tác vụ học: phát biểu quy tắc bị vi phạm, không chứa đáp án. |
| Hạ tầng lỗi | infrastructure error | Lỗi do API, mạng hoặc môi trường, không phải lỗi của tác tử; không dùng làm bằng chứng khi phân loại lỗi. |
| Đường dẫn tương đối | relative path | Dạng `workspace/x`, tính từ thư mục gốc của sandbox; dùng được ở cả công cụ tệp lẫn shell, khác với `/workspace/x` chỉ dùng được ở công cụ tệp. |
| Phình to skill | skill bloat | Thư viện skill dài và trùng lặp, làm tác tử khó chọn đúng và tốn token. |
| Giới hạn đệ quy | recursion limit | Số bước tối đa của đồ thị tác tử trong một lần chạy; chặn vòng lặp vô hạn. |
| Băm | hash | Chuỗi định danh nội dung (SHA-256); dùng để phát hiện thư mục skill bị sửa. |
| Bẫy | trap | Đặc điểm có chủ ý của tác vụ khiến cách làm ngây thơ cho kết quả sai. |
| Mô hình giả | fake model | Mô hình thay thế dùng cho test ngoại tuyến (`ScriptedChatModel`), không gọi API và không tốn token. |
| Ngoại tuyến | offline | Chạy không cần kết nối API. |
| Tính hợp lệ | validity | Mức độ kết luận của thí nghiệm đáng tin; bị ảnh hưởng bởi nhiễu, số mẫu nhỏ, thiết kế. |
