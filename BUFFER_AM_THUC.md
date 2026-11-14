# Tích hợp Buffer cho website ĂN NGON CÓ DEAL

Đã tạo cầu nối độc lập trong GitHub repository an-ngon-co-deal-content, hoàn toàn khác dự án PC GIÁ TỐT.

## Nguồn
- Website: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/
- RSS công khai: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/rss.xml
- Mã: scripts/food_buffer_rss.py
- GitHub Actions: .github/workflows/food-buffer-rss.yml

Chỉ đọc bài đã xuất bản có liên kết /bai-viet/ trên chính website ẩm thực. Kho bản nháp 2.000 bài chưa được đưa lên Facebook.

## Vận hành
Workflow chạy 09:17 và 19:17 (giờ Hà Nội), tối đa 1 bài/lần vào Buffer Queue, dừng nếu Queue có >=9 bài. Buffer xuất bản theo khung giờ đã được chủ Fanpage thiết lập. Chương trình kiểm tra kênh Facebook có đúng tên Ăn Ngon Có Deal trước khi gửi, ghi lịch sử URL để tránh trùng.

## Để bật phải hoàn thành
1. Trên Buffer: kết nối **Fanpage Ăn Ngon Có Deal**, không phải PC GIÁ TỐT.
2. Trong GitHub repo Settings > Secrets and variables > Actions:
   - Repository secret FOOD_BUFFER_API_KEY: API token Buffer, chỉ dán vào GitHub Secret, không gửi qua chat.
   - Repository variable FOOD_BUFFER_CHANNEL_ID: ID của kênh Buffer Fanpage ẩm thực, không phải ID trang PC GIÁ TỐT.
   - Repository variable FOOD_BUFFER_AUTO_QUEUE: đặt thành true sau khi kiểm thử.
3. Trong Buffer thiết lập khung giờ đăng; thử một bài trước và kiểm tra đúng Fanpage.

Khi chưa đủ cả 3 thông số, workflow chỉ kiểm tra RSS và **KHÔNG tạo bài đăng**. Không có chức năng tự trả phí, không quảng cáo, không dùng secret PC GIÁ TỐT.

Lưu ý: Mã dùng GraphQL API của Buffer, cần xác minh các trường/mutation với tài khoản thực tế khi có token. Nếu Buffer API thay đổi hoặc tài khoản không hỗ trợ quyền ghi, workflow sẽ dừng an toàn thay vì tự đăng nhầm trang. Không nên coi mã đã chạy thành công trên Buffer nếu chưa kiểm thử kết nối thực.
