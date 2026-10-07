# Báo cáo Lab: Self evolving Agentic


## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Hà Anh Tuấn | 2A202602376 | Làm cá nhân |

- Mô hình theo .env hiện tại: `openai:gpt-4o-mini`; nhiệt độ `0`; recursion_limit `60`. Cấu hình hiện tại không thay thế nhật ký cấu hình lịch sử.
- Deep Agents `0.7.21`; trace ghi Linux/WSL, Python `3.14.4`; chạy trực tiếp trong WSL.
- Kết quả lưu: 21 lượt tác vụ (18 chính thức, 3 thử skill) và 1 lượt curator được xác nhận; tổng ngân sách chưa được cung cấp.
- Commit của tag `freeze`: `3a09129858303e477b3fcec3b0519df8f54b0561`.

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

Các giả thuyết dưới đây được viết từ kết quả tác vụ học ở mục 4–6, trước khi xem điểm tác vụ đánh giá. Giữ nguyên giả thuyết khi có kết quả đánh giá; kết quả trái dự đoán vẫn là dữ liệu hợp lệ. Đo bằng điểm trung bình ba tác vụ đánh giá; tách check kỹ thuật/quy ước, đồng thời ghi nhận token, lỗi runner và việc đọc skill/giao việc.

- H1 (subagents so với baseline): Trên tác vụ đánh giá, dự đoán điểm trung bình subagents không cao hơn baseline; baseline được dự đoán đạt điểm cao nhất hoặc đồng hạng cao nhất trong ba điều kiện. Căn cứ: ở tác vụ học, subagents đạt trung bình 16,7% so với baseline 17,5%, cùng đạt 5/27 check và 0/9 check quy ước. Chỉ data-learn thực sự gọi subagent (2 lần), nhưng điểm giảm từ 1/8 xuống 0/8 và token tăng gần 4 lần; kết quả giao việc chưa được kiểm chứng. code-learn tăng một check nhưng không gọi subagent, nên chưa có bằng chứng cải thiện do đa tác tử. H1 được ủng hộ nếu điểm trung bình subagents trên eval nhỏ hơn hoặc bằng baseline; nếu cao hơn thì kết quả trái dự đoán. Chi phí được báo cáo riêng vì tổng token học chịu ảnh hưởng của baseline bị recursion limit.
- H2 (skills-auto so với baseline): Với bộ hai skill hiện tại được đóng băng, dự đoán điểm trung bình skills-auto trên tác vụ đánh giá không cao hơn baseline và không cải thiện số check quy ước đạt. Căn cứ: ở tác vụ học, skills-auto đạt 13,3% so với baseline 17,5%, check kỹ thuật 4/18 so với 5/18, quy ước cùng 0/9; cả ba bản ghi skills_read=0, riêng data-learn thiếu trace và bị recursion limit nên mức độ quan sát hạn chế. Skill log chưa nêu rõ một số quy ước, skill bảo vệ test có description khá hẹp, và bộ skill chưa bao phủ lỗi thực thi/phân tích dữ liệu. Theo phần “Lưu ý khoa học” trong guides/pseudocode/04_curator.md, SkillsBench được tóm tắt là skill tự sinh trung bình không có lợi; đây là căn cứ tham khảo, không phải bảo đảm cho lab này. H2 được kiểm tra bằng chênh lệch điểm trung bình và số check quy ước đạt giữa skills-auto và baseline trên eval; nếu skills-auto cải thiện thì cần dùng trace và skills_read để giải thích.
- H3 (tác vụ học so với tác vụ đánh giá): Dự đoán bộ skill hiện tại không tạo lợi ích chuyển giao dương trên tác vụ đánh giá. Gọi Δlearn và Δeval là chênh lệch điểm trung bình skills-auto trừ baseline trên từng nhóm; dự đoán Δeval ≤ 0, còn Δlearn cũng không dương trong lần chạy học sau đóng băng. Căn cứ: lượt thử Phần 3.4 có Δlearn khoảng -4,2 điểm phần trăm, chưa ghi nhận đọc skill và không cải thiện check quy ước. Skill log bám một schema cụ thể, skill bảo vệ test chỉ bao phủ một phần yêu cầu; chưa có căn cứ để kỳ vọng chúng tự xử lý quy ước mới. Theo tóm tắt SkillEvolBench trong guides/pseudocode/04_curator.md, lợi ích trên tác vụ học có thể không chuyển sang tác vụ mới. Nếu sau đóng băng có Δlearn > 0 nhưng Δeval ≤ 0, đó là dấu hiệu lợi ích chưa chuyển giao, phù hợp khả năng quá khớp nhưng chưa đủ chứng minh vì chỉ chạy một lần. Nếu Δeval > 0, dự đoán chính của H3 bị bác bỏ; cần đối chiếu trace để phân biệt skill được áp dụng với nhiễu mô hình.

Không dự đoán điểm tuyệt đối của eval hoặc dùng kết quả eval để điều chỉnh skill. Khi đánh giá, so sánh thêm số check đạt và đánh dấu các lần bị recursion limit; không kết luận ý nghĩa thống kê từ ba tác vụ và một lần chạy mỗi cấu hình. Δlearn chính thức dùng lần chạy học sau đóng băng; kết quả Phần 3.4 được giữ riêng để quan sát nhiễu.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có các công cụ: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute`, `task`. Công cụ `execute` cho phép chạy lệnh shell trong sandbox.
2. Subagent `general-purpose` dùng để nghiên cứu câu hỏi phức tạp, tìm tệp/nội dung và thực hiện tác vụ nhiều bước; có quyền dùng cùng bộ công cụ với tác tử chính. Mỗi lần gọi mặc định không lưu trạng thái: subagent chỉ thấy prompt được giao, không tự nhận lịch sử hội thoại của tác tử chính, và trả về một báo cáo cuối cùng.
3. System prompt mặc định rỗng (`''`); hướng dẫn hành vi nằm trong mô tả công cụ. Trích từ `task`: “The agent's report is not shown to the user; relay a summary yourself.” Trích từ `execute`: “Use absolute paths and avoid `cd` so the working directory stays stable; use the optional timeout to override the default.”

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

Phân tích chỉ sử dụng ba tác vụ học. Phân loại dưới đây gán một nhóm chính cho mỗi check; các check có thể cùng thất bại do một nguyên nhân chung.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ detail hoặc vết) |
|---|---|---|---|
| code-learn | `tests_not_modified` | A | the original files in tests/ must not be modified (new test files are allowed); đề yêu cầu không sửa tests/. Trace baseline không ghi thao tác, nên nguyên nhân chỉ là suy luận từ check. |
| code-learn | `parse_price_all_formats` | D | wrong for: ['(12.00)']; bỏ sót định dạng giá âm bằng dấu ngoặc. |
| code-learn | `csv_quoting_follows_docstring` | D | to_csv_row returned 'Desk, large "oak",10.00,2'; bỏ sót escape dấu phẩy và dấu nháy kép. |
| code-learn | `rule_type_hints` | E | RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value. |
| code-learn | `rule_regression_tests` | E | RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass. |
| code-learn | `rule_changelog` | E | RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>' (at least 3 bullets). |
| data-learn | `north_q1_revenue` | B | north_q1_revenue: wrong value (got 0); trace: ModuleNotFoundError: pandas, sau đó write_file ghi các giá trị 0 chưa được tính thành công. |
| data-learn | `north_q1_orders` | B | north_q1_orders: wrong value (got 0); trace: ModuleNotFoundError: pandas, sau đó write_file ghi các giá trị 0 chưa được tính thành công. |
| data-learn | `missing_amount_orders` | B | missing_amount_orders: wrong value (got 0); trace: ModuleNotFoundError: pandas, sau đó write_file ghi các giá trị 0 chưa được tính thành công. |
| data-learn | `duplicate_rows_removed` | B | duplicate_rows_removed: wrong value (got 0); trace: ModuleNotFoundError: pandas, sau đó write_file ghi các giá trị 0 chưa được tính thành công. |
| data-learn | `rule_money_in_cents` | E | RULE: money values in answer.json are integer cents (1606.67 USD is written 160667). |
| data-learn | `rule_meta_block` | E | RULE: answer.json has an object `meta` = {"source": <input file name>, "rows_in": <number of data rows in the input file, duplicates included>, "rows_used": <number of distinct orders with a known amount>}. |
| data-learn | `rule_clean_csv` | E | RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; one row per distinct order with a known amount; timestamp_utc as YYYY-MM-DDTHH:MM:SSZ (UTC); region in canonical spelling (North, South, East, West); amount in integer cents. |
| logs-learn | `valid_structure` | B | FileNotFoundError: workspace/errors.json; trace chỉ có 2 read_file, không có bước ghi/kiểm tra đầu ra. |
| logs-learn | `entry_count` | B | FileNotFoundError: workspace/errors.json; trace chỉ có 2 read_file, không có bước ghi/kiểm tra đầu ra. |
| logs-learn | `timestamps_utc` | B | FileNotFoundError: workspace/errors.json; trace chỉ có 2 read_file, không có bước ghi/kiểm tra đầu ra. |
| logs-learn | `exception_fields` | B | FileNotFoundError: workspace/errors.json; trace chỉ có 2 read_file, không có bước ghi/kiểm tra đầu ra. |
| logs-learn | `repeat_counts` | B | FileNotFoundError: workspace/errors.json; trace chỉ có 2 read_file, không có bước ghi/kiểm tra đầu ra. |
| logs-learn | `counts_by_service` | B | FileNotFoundError: workspace/errors.json; trace chỉ có 2 read_file, không có bước ghi/kiểm tra đầu ra. |
| logs-learn | `rule_service_names` | E | Thiếu workspace/errors.json; chưa đủ bằng chứng đánh giá riêng quy ước này. |
| logs-learn | `rule_sorted_errors` | E | Thiếu workspace/errors.json; chưa đủ bằng chứng đánh giá riêng quy ước này. |
| logs-learn | `rule_schema_header` | E | Thiếu workspace/errors.json; chưa đủ bằng chứng đánh giá riêng quy ước này. |

Baseline đạt 5/27 check: code-learn 4/10, data-learn 1/8, logs-learn 0/9. Check kỹ thuật đạt 5/18; check quy ước đạt 0/9. Trong 22 check thất bại, nhóm B có 10, E có 9, D có 2 và A có 1. Nhóm B chiếm nhiều nhất theo cách phân loại này, nhưng 6 check kỹ thuật của logs-learn cùng bị chặn bởi một tệp đầu ra thiếu; không xem đó là 6 nguyên nhân độc lập. Không có bằng chứng đủ mạnh để kết luận nhóm C. Không gán F chỉ vì số liệu sai: answer.json thực sự được tạo; tuy nhiên tuyên bố đã làm sạch dữ liệu trong data-learn không được các lệnh thực thi thành công hỗ trợ.

Với data-learn, ngoài lỗi thực thi còn có rủi ro nhóm D trong đoạn mã dự định chạy: drop_duplicates() không chỉ định order_id, đếm trùng sau khi đã xóa trùng, và parse ngày hỗn hợp bằng errors='coerce' mà không kiểm tra dữ liệu mất. Đây là rủi ro quan sát từ mã trong trace, không khẳng định mã đã chạy thành công. top_region đạt check nhưng được ghi trực tiếp sau lỗi pandas, nên chưa chứng minh phép tính đúng.

Skill có thể yêu cầu đọc đặc tả, kiểm tra thư viện hoặc dùng thư viện chuẩn, xử lý lỗi shell trước khi tiếp tục, tính và đối chiếu số liệu, xác nhận tệp đầu ra tồn tại và đọc lại trước khi kết thúc. Skill về ngày/UTC, khóa khử trùng, dữ liệu thiếu và CSV quoting có thể giảm nhóm D. Skill quy ước có thể bổ sung các yêu cầu E rút ra từ phản hồi tác vụ học; không đảm bảo giải quyết được việc chạy bị cắt hoặc thiếu đầu ra.

Baseline code-learn bị GraphRecursionError ở giới hạn 60 bước: 196.394 token, 575,2 giây, final_message rỗng. Điểm 4/10 phản ánh trạng thái tệp khi bị dừng, không phải một lần chạy hoàn tất. Trace lưu chỉ có đề bài, tool_calls=0; vì vậy không thể xác định thao tác lặp hay khẳng định agent không dùng công cụ trong suốt lần chạy. Giữ nguyên kết quả, chưa chạy lại; ghi nhận hạn chế khi so sánh điều kiện.

## 5. Điều kiện `subagents` (Phần 2.3)

Hai subagent được định nghĩa trong src/lab/subagents.py: explorer đọc yêu cầu/tệp và đề xuất bước tiếp theo, không sửa tệp; reviewer đối chiếu kết quả với yêu cầu và chạy kiểm tra khi cần, không sửa tệp. Thiết kế nhằm hỗ trợ điều tra trước khi sửa và đánh giá độc lập sau khi sửa.

| Tác vụ | subagent_calls | Subagent thực tế | Nhận xét từ trace |
|---|---:|---|---|
| code-learn | 0 | Không gọi | Tác tử chính tự đọc, sửa và chạy pytest; không có task. |
| data-learn | 2 | general-purpose, 2 lần | Hai lời giao việc gần như giống nhau; không gọi explorer hoặc reviewer. |
| logs-learn | 0 | Không gọi | Trace chỉ có hai lần đọc app.log; không tạo errors.json. |

subagent_calls=0 là kết quả hợp lệ. Với code-learn, tác tử chính trực tiếp thực hiện công việc nên có thể đã thấy không cần giao việc; đây là suy luận, trace không nêu lý do. Với logs-learn, bằng chứng quá ít để xác định lý do không giao việc. Không suy ra cả ba tác vụ có giao việc chỉ từ tên điều kiện subagents.

Lời giao việc data-learn có đường dẫn CSV, năm chỉ số, khoảng thời gian UTC, yêu cầu chuẩn hóa vùng, loại trùng và xử lý -999. Tuy nhiên không chuyển đầy đủ mô tả ba định dạng ngày trong README, không nói rõ khử trùng theo order_id và không nhắc các quy ước Acme. Quy ước chưa được nêu chi tiết trong đề nên không kết luận tác tử cố ý bỏ qua chúng. Lời giao việc yêu cầu general-purpose ghi answer.json thay vì dùng explorer để khảo sát hoặc reviewer để kiểm tra.

Lần gọi thứ nhất trả hướng dẫn pandas và nói không thể thực thi; lần thứ hai báo phân tích thất bại do môi trường. Trace chính có hai lần execute cùng một lệnh một dòng chứa `; with open(...)`, đều báo lỗi cú pháp. Sau đó tác tử chính ghi trực tiếp answer.json với các giá trị 0 và top_region='West', không có bước tính thành công hoặc đọc/kiểm tra lại đầu ra. Vì vậy báo cáo subagent chưa được kiểm chứng trước khi dùng. Không thể xác minh các thao tác nội bộ của subagent vì trace chỉ lưu luồng chính; lời báo lỗi môi trường của subagent cũng chưa phải chẩn đoán độc lập.

| Tác vụ | Điểm baseline → subagents | Token baseline | Token subagents | Thay đổi token | Giây baseline → subagents |
|---|---|---:|---:|---:|---|
| code-learn | 4/10 → 5/10 | 196.394 | 67.430 | -65,7% | 575,2 → 133,8 |
| data-learn | 1/8 → 0/8 | 26.156 | 104.031 | +297,7% | 19,2 → 72,2 |
| logs-learn | 0/9 → 0/9 | 29.140 | 29.425 | +1,0% | 182,2 → 172,5 |

Tổng token baseline là 251.690, subagents là 200.886; trung bình lần lượt 83.896,7 và 66.962,0 (-20,2%). Tổng thời gian lần lượt 776,6 và 378,5 giây (-51,3%). Điểm trung bình theo tác vụ là 17,5% và 16,7%; tổng số check đạt cùng bằng 5/27. Check kỹ thuật cùng đạt 5/18, quy ước cùng đạt 0/9. Các số này là mô tả ba lần chạy học, chưa phải kết luận về hiệu quả đa tác tử.

Baseline code-learn bị cắt bởi recursion limit và chiếm phần lớn chi phí baseline, trong khi code-learn ở điều kiện subagents không thực sự gọi subagent. Do đó không quy việc giảm tổng token/thời gian hoặc tăng 1 check của code-learn cho cơ chế giao việc. data-learn thực sự gọi subagent nhưng tốn gần 4 lần token và điểm giảm; trong lần chạy này chưa thấy lợi ích từ giao việc. Mỗi điều kiện chỉ có một lần chạy, nên chưa tách được nhiễu mô hình.

Quan sát bổ sung: code-learn ở điều kiện subagents có lỗi sửa đồng thời cùng tệp và String not found; sau đó tác tử phục hồi và chạy visible tests đạt 6 passed. Tuy vậy check tests_not_modified và csv_quoting_follows_docstring vẫn thất bại. Trace không ghi sửa tests/, nên cần giữ sự khác biệt giữa kết quả checker và bằng chứng thao tác, không suy đoán nguyên nhân. logs-learn ở cả hai điều kiện có error=null nhưng final_message rỗng và thiếu errors.json: không có exception runner không đồng nghĩa hoàn thành tác vụ.

## 6. Self-evolving: skill do curator sinh (Phần 3)

Đã xác nhận một lần chạy `python -m lab.curator` theo thông tin người thực hiện; kết quả hiện có gồm 2 skill. Chưa có thông tin về lần chạy lại hoặc skill từng bị xóa. Trong lần đánh giá này giữ cả hai skill để kiểm chứng ở Phần 3.4, không sửa tay nội dung và không chạy lại curator.

Cả hai tệp đều được kiểm tra bằng `validate_skill(text, expected_name)` và trả về danh sách vấn đề rỗng: frontmatter, tên khối, độ dài và kiểm tra định danh đánh giá đều hợp lệ. Đây là kiểm tra định dạng và định danh, không chứng minh skill đúng về nội dung hoặc hiệu quả.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `ensure-log-output-compliance` | Áp dụng cho phân tích log cùng schema; không có tên tác vụ, tệp đầu vào hay đáp án cụ thể. Tuy nhiên các khóa `errors`, `counts_by_service`, `timestamp_utc` và cách lọc ERROR/CRITICAL bám sát yêu cầu logs-learn, nên khả năng chuyển sang định dạng log khác còn hạn chế. | Các bước lọc mức lỗi, UTC, viết hoa level và lấy dòng cuối traceback phù hợp đề học. Chưa nêu rõ `repeat_count = 1 + tổng N`, cách cộng `counts_by_service`, chuẩn hóa tên dịch vụ, thứ tự sắp xếp và header schema. Bước 8 chỉ yêu cầu kiểm tra quy ước chung, không cung cấp các quy tắc đó. Không yêu cầu xác nhận tệp đầu ra tồn tại, là nguyên nhân trực tiếp của toàn bộ check logs-learn thất bại. | 12 dòng toàn tệp, 8 dòng thân; ngắn, dạng danh sách mệnh lệnh. `description` bắt đầu bằng “Use when”, nêu tạo đầu ra log nhưng chưa rõ tình huống phân tích/triage log. Cả ba tác vụ đều ghi `skills_read=0`; trace code/log không có bước đọc skill, trace data rỗng do lần chạy bị lỗi. |
| `prevent-test-modification` | Tổng quát trong tác vụ sửa lỗi có yêu cầu giữ nguyên test; không chứa tên hàm, đáp án hoặc chi tiết riêng của code-learn. Tuy nhiên quy tắc “Always create new test files” được áp dụng tuyệt đối, rộng hơn điều kiện của tác vụ học. | Phù hợp yêu cầu không sửa test hiện có và tạo test bổ sung. Chạy lại test giúp giảm lỗi thiếu kiểm chứng. Hạn chế: trong dự án cho phép cập nhật test, cấm sửa test cũ có thể không phù hợp; “named appropriately” chưa cụ thể; không yêu cầu một test cho mỗi lỗi hoặc đúng tệp regression/changelog theo quy ước Acme. Không bao phủ type hints, giá âm hay CSV quoting. | 9 dòng toàn tệp, 5 dòng thân; ngắn, dạng danh sách mệnh lệnh. `description` bắt đầu bằng “Use when” nhưng tập trung sửa/tạo test, nên tác vụ sửa mã nguồn có thể không kích hoạt đọc skill. Cả ba tác vụ đều ghi `skills_read=0`; trace code/log không có bước đọc skill, trace data rỗng do lần chạy bị lỗi. |

Nhận xét: bộ skill chỉ bao phủ việc bảo vệ test và một phần cấu trúc đầu ra log. Chưa có skill riêng xử lý lỗi thư viện/thực thi, kiểm tra đầu ra trước khi kết thúc, ngày hỗn hợp/UTC và khử trùng dữ liệu; các lỗi baseline data-learn còn ít được bao phủ. Vì logs-learn thiếu tệp đầu ra, feedback của các check quy ước chỉ là FileNotFoundError, nên dữ liệu phản hồi không cung cấp rõ các quy tắc Acme cho curator. Do đó không kỳ vọng việc vượt qua validator tự động bảo đảm cải thiện điểm.

Không thấy tên tác vụ đánh giá hoặc đáp án cụ thể trong hai skill; chỉ kiểm tra trên skill sinh ra và tài liệu tác vụ học, không đọc kết quả tác vụ đánh giá. Giữ nguyên đầu ra để quan sát hiệu quả; nếu các quy tắc quá rộng gây lỗi khi chạy Phần 3.4, cần ghi bằng chứng và cân nhắc xóa hoặc chạy lại curator theo GUIDE, thay vì sửa tay.

### Kiểm tra sử dụng skill trên tác vụ học (Phần 3.4)

Kết quả thử tại results/skills-auto-dev: đã chạy xong `python -m lab.runner --condition skills-auto --tasks learn` và có đủ run.json/trace.md của ba tác vụ học. Một lần chạy bị recursion limit; kết quả được giữ nguyên để phân tích, chưa chạy lại.

| Tác vụ | Điểm baseline → skills-auto | Token skills-auto | Thời gian | skills_read | error | skills_modified |
|---|---|---:|---:|---:|---|---|
| code-learn | 4/10 → 4/10 | 59.898 | 80,8 giây | 0 | null | false |
| data-learn | 1/8 → 0/8 | 513.839 | 174,5 giây | 0 | GraphRecursionError (60 bước) | false |
| logs-learn | 0/9 → 0/9 | 30.753 | 175,7 giây | 0 | null | false |

Ở code-learn, cả hai skill chưa được đọc: skills_read=0 và trace chỉ ghi đọc mã nguồn/test, không có read_file tới SKILL.md. Vì vậy chưa có bằng chứng quy trình của skill được áp dụng. Skill prevent-test-modification có description tập trung vào sửa/tạo test, trong khi tác tử chủ yếu sửa mã nguồn; đây là một khả năng giải thích việc không đọc, không phải lý do đã được mô hình xác nhận. Skill log không phù hợp trực tiếp với tác vụ code.

Các check đạt là visible_suite_passes, other_caller_fixed, discount_rounds_half_up và low_stock_follows_docstring (kỹ thuật 4/7; quy ước 0/3). Các check thất bại: tests_not_modified; parse_price_all_formats (bỏ sót '(12.00)'); csv_quoting_follows_docstring (không escape tên chứa dấu phẩy/nháy kép); rule_type_hints; rule_regression_tests; rule_changelog. Tập check đạt/thất bại giống baseline code-learn. Không gán các check đạt cho lợi ích của skill vì agent chưa đọc skill.

Trace cho thấy tác tử đọc docstring và test hiện có, sửa pricing/report rồi chạy visible tests đạt 6 passed sau khi xử lý lỗi import và lỗi cú pháp `return return`. Tuy vậy không đối chiếu hết các tình huống trong docstring (giá âm và CSV quoting). Không có thao tác ghi/sửa tests/ trong trace, nhưng checker tests_not_modified vẫn thất bại; chưa xác định nguyên nhân của sự khác biệt này. Tác tử không tạo regression test hoặc changelog theo quy ước. Bước chạy lại test phù hợp một chỉ dẫn của prevent-test-modification, nhưng cũng được yêu cầu bởi tác vụ, nên không chứng minh agent đã áp dụng skill.

So với baseline code-learn, số token giảm từ 196.394 xuống 59.898 (-69,5%) và thời gian từ 575,2 xuống 80,8 giây (-86,0%), điểm giữ nguyên 4/10. So với subagents code-learn, điểm giảm từ 5/10 xuống 4/10. Baseline bị recursion limit, còn lần skills-auto kết thúc với error=null; cùng với skills_read=0 và chỉ một lần chạy, chưa thể quy thay đổi chi phí cho skill. Các thống kê đủ ba tác vụ được trình bày dưới đây.

Bộ skill không bị thay đổi trong lần chạy (skills_modified=false); run ghi skills_sha256=`34fb336a49b92f9b7e418841e09c0476030922bfe2b4234c70e3250ae4a4b5c8`. So sánh với lần sau đóng băng được trình bày ở mục 8.6. Đã đủ dữ liệu thử nghiệm Phần 3.4; riêng data-learn là kết quả khi bị dừng, không phải một lần hoàn thành bình thường. Kết quả thử đã được sao lưu tại results/skills-auto-dev trước lần chạy chính thức.

#### Kết quả data-learn và logs-learn

skills-auto data-learn đạt 0/8 và bị GraphRecursionError tại giới hạn 60 bước, dùng 513.839 token trong 174,5 giây; final_message rỗng. Bảy check báo thiếu workspace/answer.json, rule_clean_csv cũng thất bại. Trace.md rỗng, tool_calls=0 và skills_read=0 trong bản ghi; không đủ bằng chứng xác định thao tác lặp hoặc khẳng định mô hình chưa thực hiện công cụ/đọc skill trong toàn bộ lần chạy. Chỉ kết luận đầu ra cần thiết không được tạo và không có bằng chứng sử dụng skill được lưu. So với baseline data-learn (1/8, 26.156 token, 19,2 giây), điểm giảm một check và token tăng khoảng 19,64 lần. Không quy toàn bộ tăng chi phí cho nội dung skill vì chưa có bằng chứng đọc skill và lần chạy bị cắt.

skills-auto logs-learn đạt 0/9, dùng 30.753 token trong 175,7 giây, error=null nhưng final_message rỗng. Cả 9 check báo FileNotFoundError với workspace/errors.json. Trace có hai read_file app.log, không đọc README hoặc SKILL.md, không ghi/kiểm tra đầu ra. Skill ensure-log-output-compliance phù hợp miền tác vụ nhưng chưa được đọc; do đó chưa thể đánh giá việc làm theo 8 chỉ dẫn của skill. So với baseline logs-learn, điểm vẫn 0/9, token tăng 5,5% và thời gian giảm 3,6%. error=null chỉ nói runner không ghi exception, không chứng minh tác vụ hoàn thành.

| Thống kê ba tác vụ học | baseline | subagents | skills-auto (Phần 3.4) |
|---|---:|---:|---:|
| Check đạt / tổng | 5/27 | 5/27 | 4/27 |
| Check kỹ thuật đạt / tổng | 5/18 | 5/18 | 4/18 |
| Check quy ước đạt / tổng | 0/9 | 0/9 | 0/9 |
| Điểm trung bình theo tác vụ | 17,5% | 16,7% | 13,3% |
| Tổng token | 251.690 | 200.886 | 604.490 |
| Token trung bình | 83.896,7 | 66.962,0 | 201.496,7 |
| Tổng thời gian (giây) | 776,6 | 378,5 | 431,0 |
| Lần chạy có lỗi runner | 1 | 0 | 1 |
| Lần chạy ghi nhận đọc skill | 0 | 0 | 0 |

So với baseline, skills-auto có điểm trung bình giảm khoảng 4,2 điểm phần trăm và tổng token tăng 140,2%; data-learn chiếm 85,0% tổng token skills-auto. Các lần chạy đều ghi cùng skills_sha256 và skills_modified=false. Chưa thấy bằng chứng skill cải thiện check kỹ thuật hoặc quy ước trong lượt thử này. Không đồng nhất “chưa đọc skill” với “skill sai”: code/log có trace hỗ trợ việc không đọc, còn data thiếu trace nên mức độ quan sát hạn chế. Kết quả chỉ gồm tác vụ học, mỗi cấu hình một lần; cả baseline và skills-auto đều có một tác vụ bị recursion limit, nên chưa thể kết luận hiệu quả trên tác vụ mới hay khác biệt có tính ổn định.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng chính dùng 18 kết quả trong results/baseline, results/subagents và results/skills-auto. Ba kết quả thử Phần 3.4 được giữ riêng tại results/skills-auto-dev.

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 4/10 | 5/10 | 3/10 |
| data-learn | 1/8 | 0/8 | 1/8 |
| logs-learn | 0/9 | 0/9 | 0/9 |
| code-eval | 0/11 | 1/11 | 1/11 |
| data-eval | 0/9 | 0/9 | 3/9 |
| logs-eval | 1/10 | 1/10 | 1/10 |
| **Mean score - learning tasks** | 0.18 | 0.17 | 0.14 |
| **Mean score - evaluation tasks** | 0.03 | 0.06 | 0.17 |
| **Mean tokens per run** | 88,635 | 139,757 | 71,285 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

Thống kê từ scripts/check_breakdown.py:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval      1/18         0/12          93,374      0/3
baseline      learn     5/18         0/9           83,896      0/3
subagents     eval      2/18         0/12         212,552      0/3
subagents     learn     5/18         0/9           66,962      0/3
skills-auto   eval      5/18         0/12         105,855      0/3
skills-auto   learn     4/18         0/9           36,716      0/3
```

Có 5/18 lần chính thức bị GraphRecursionError ở giới hạn 60:

| Điều kiện / tác vụ | Điểm | Token | Giây |
|---|---:|---:|---:|
| baseline / code-learn | 4/10 | 196.394 | 575,2 |
| baseline / code-eval | 0/11 | 218.352 | 707,1 |
| subagents / code-eval | 1/11 | 210.070 | 641,0 |
| subagents / data-eval | 0/9 | 409.413 | 111,2 |
| skills-auto / code-eval | 1/11 | 149.242 | 119,8 |

Giữ nguyên kết quả khi bị dừng, chưa chạy lại và không đổi giới hạn giữa điều kiện. Trace các lượt lỗi rỗng nên không xác định được thao tác lặp. Lượt thử skills-auto-dev/data-learn cũng bị lỗi, nhưng không tính vào bảng chính. Tất cả 18 bản ghi có skills_modified=false; không tác vụ nào đạt toàn bộ check.

Lệnh `python scripts/verify_freeze.py` trả về `checked 6 runs of skill conditions: OK`, xác nhận cả sáu lượt chạy `skills-auto` tuân thủ quy trình đóng băng: giả thuyết được commit trước tag `freeze`, bộ skill không thay đổi từ mốc đóng băng, các lượt chạy dùng đúng bộ skill đã chốt và có `skills_modified=false`.

## 8. Phân tích

1. **Điểm và giả thuyết.** Điểm trung bình baseline/subagents/skills-auto trên học là 17,50% / 16,67% / 14,17%; trên eval là 3,33% / 6,36% / 17,47%. Hai điều kiện thử nghiệm đều không cải thiện điểm học so với baseline; subagents cải thiện eval 3,03 điểm phần trăm, skills-auto cải thiện 14,14 điểm phần trăm. Không có trường hợp cải thiện học nhưng không cải thiện eval trong bảng chính. H1 bị bác bỏ theo điểm quan sát; phần dự đoán điểm của H2 bị bác bỏ nhưng dự đoán không cải thiện quy ước được ủng hộ. Dự đoán Δeval ≤ 0 của H3 bị bác bỏ, còn Δlearn ≤ 0 phù hợp dữ liệu (khoảng -3,33 điểm phần trăm). Giữ nguyên giả thuyết ban đầu; khác biệt quan sát chưa chứng minh quan hệ nhân quả hoặc ý nghĩa thống kê.

2. **Kỹ thuật và quy ước.** Eval kỹ thuật đạt 1/18, 2/18 và 5/18; học kỹ thuật đạt 5/18, 5/18 và 4/18. Quy ước đều 0/12 trên eval và 0/9 trên học. skills-auto/data-eval đạt top_category, missing_total_orders và duplicate_events_removed; code-eval đạt add_slot_no_shared_state; logs-eval chỉ đạt valid_structure. Cải thiện nằm ở check kỹ thuật, nhưng chưa có bằng chứng skill giúp trực tiếp. Các quy ước mới rule_version_bump, rule_sorted_keys_format và rule_source_line đều không đạt. Bộ skill không cung cấp rõ các quy tắc này và chưa ghi nhận đọc; vượt qua validator định dạng không bảo đảm chuyển giao quy ước.

3. **Trace và sử dụng skill.** Không thể nêu một check được chứng minh là do skill giúp đạt: cả 6 bản ghi skills-auto có skills_read=0; các trace không rỗng không ghi đọc SKILL.md. Ví dụ top_category đạt ở data-eval: trace cho thấy đọc README, dùng thư viện chuẩn, chuẩn hóa category bằng strip().lower(), xử lý chuỗi tiền và khử trùng theo id. Đây là hành vi đúng một phần, không chứng minh áp dụng skill. Hai check tháng UTC vẫn thất bại: mã hiển thị dùng datetime.fromisoformat rồi kiểm tra year/month mà chưa chuyển UTC. Lệnh trong trace bị cắt nên không tái dựng toàn bộ chương trình. logs-eval đổi một số timestamp bằng date và ghi errors.json nên valid_structure đạt; các check còn lại thất bại. Skill log chỉ nêu lọc ERROR/CRITICAL trong khi đề eval có mức khác: có nguy cơ bỏ sót nếu áp dụng máy móc, nhưng không có bằng chứng agent đã đọc skill gây lỗi. skills-auto/data-learn gặp ModuleNotFoundError: pandas rồi ghi placeholder; top_region đạt chưa chứng minh tính toán đúng. Trace rỗng ở lượt recursion limit làm giới hạn suy luận từ skills_read=0.

4. **Chi phí.** Token trung bình trên cả 6 tác vụ: baseline 88.635,5; subagents 139.757,3; skills-auto 71.285,8. Tổng token tương ứng 531.813 / 838.544 / 427.715. Dùng tổng check đạt trên mỗi 100.000 token, baseline đạt 6 check → 1,13; subagents 7 → 0,83; skills-auto 9 → 2,10. Trên eval riêng, chỉ số lần lượt khoảng 0,36 / 0,31 / 1,57. Chỉ số coi mọi check trọng số bằng nhau; không phản ánh hoàn thành đầy đủ và không thay thế chi phí tiền. skills-auto tốt nhất theo chỉ số này trong lượt chính thức, nhưng chưa quy lợi ích cho nội dung skill. Subagents tăng tổng token khoảng 57,7% so với baseline để tăng 1 check; chưa chứng minh đáng chi phí. Các lượt bị cắt tác động mạnh tới kết quả.

5. **Rò rỉ và quá khớp.** Curator chỉ nhận role=learn; hai skill hợp lệ theo validator, không chứa định danh eval hay đáp án cụ thể quan sát được. Giả thuyết đã commit trước freeze; skill giữ nguyên; kết quả thử tách riêng. Không dùng điểm eval để sửa skill hoặc giả thuyết. Skill log bám schema học nên có nguy cơ phạm vi quá hẹp, nhưng chưa chứng minh quá khớp do dùng skill vì chưa ghi nhận đọc skill và eval còn cao hơn học. Validator định danh không phát hiện mọi dạng rò rỉ ngữ nghĩa.

6. **Nhiễu.** Cùng hash skill, điểm Phần 3.4 → chính thức là code-learn 4/10 → 3/10 (-10 điểm phần trăm), data-learn 0/8 → 1/8 (+12,5), logs-learn 0/9 → 0/9. Trung bình học tăng 13,33% → 14,17% (+0,83 điểm phần trăm), nhưng biến động theo tác vụ triệt tiêu nhau. Token học giảm 604.490 → 110.150, chủ yếu vì data-learn thử bị recursion limit còn chính thức không bị. Skill không đổi nên không coi chênh lệch là học thêm hoặc skill tốt hơn. Chênh lệch nhỏ 1 check cần diễn giải thận trọng; chưa có đủ lần lặp để đo độ biến thiên.

## 9. Hạn chế và tính hợp lệ

1. Chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy chính thức một lần; không có khoảng tin cậy, khó khái quát chênh lệch nhỏ.
2. Có 5/18 lượt chính thức bị recursion limit, trace rỗng; điểm là trạng thái khi bị dừng, làm nhiễu so sánh chất lượng và chi phí.
3. Không lượt skills-auto nào ghi nhận đọc skill. Thí nghiệm đo điều kiện có cung cấp skill, chưa kiểm chứng hiệu quả khi skill được đọc/làm theo; lượt thiếu trace còn hạn chế đo lường.
4. Shell agent thiếu pandas, có đầu ra thiếu hoặc placeholder; điểm thấp phản ánh cả môi trường và quy trình thực thi, không chỉ năng lực giải bài.
5. Quy ước do lab thiết kế và chỉ một mô hình/cấu hình; kết quả không đại diện mọi mô hình hay dự án.

## 10. Kết luận

skills-auto có điểm eval trung bình cao nhất (17,47%) và hiệu quả check/token tốt nhất trong lượt chính thức, nhưng điểm học thấp hơn baseline. Không điều kiện nào đạt check quy ước hoặc hoàn thành trọn vẹn một tác vụ. Chưa có bằng chứng cải thiện do đọc skill, và recursion limit làm hạn chế kết luận. Subagents tốn nhiều token hơn baseline mà chỉ tăng một check tổng thể, nên chưa chứng minh lợi ích chi phí. Thí nghiệm tiếp theo nên kiểm tra kích hoạt/đọc skill, môi trường shell và lưu trace khi lỗi, rồi chạy lặp một thiết kế mới; không chỉnh bộ skill đã freeze hiện tại.

## Phụ lục

Lệnh đã chạy theo thông tin người dùng và kết quả lưu:

```bash
python -m pytest tests/test_02_agent.py tests/test_03_runner.py
python -m lab.runner --condition baseline --tasks data-learn
python -m lab.runner --condition baseline --tasks code-learn logs-learn
python -m lab.runner --condition subagents --tasks learn
python -m lab.curator
python -m lab.runner --condition skills-auto --tasks learn
git add -A && git commit -m "hypotheses"
git commit --allow-empty -m "freeze skills"
git tag freeze
mv results/skills-auto results/skills-auto-dev
python -m lab.runner --condition baseline --tasks eval
python -m lab.runner --condition subagents --tasks eval
python -m lab.runner --condition skills-auto --tasks all
python scripts/verify_freeze.py
python -m lab.compare > report/table.md
python scripts/check_breakdown.py
```

Người thực hiện báo 15 passed cho test_02/test_03 trên Ubuntu. Có 21 kết quả tác vụ lưu (18 chính thức và 3 thử Phần 3.4), cộng một lần curator được xác nhận; chưa có token curator hoặc lịch sử đầy đủ để tính ngân sách còn lại. Chưa thực hiện thử thách mở rộng. Giữ kết quả lỗi, chưa chạy lại; không sửa tay skill. Mục 6 ghi lịch sử trước đóng băng, khác bảng chính mục 7.
