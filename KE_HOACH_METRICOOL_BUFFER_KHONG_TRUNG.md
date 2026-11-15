# PHÂN CÔNG BUFFER VÀ METRICOOL — ĂN NGON CÓ DEAL

Cập nhật: 2026-11-15. **Bản cấu hình kế hoạch; chưa bật đăng tự động.**

Website: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/
RSS bài công khai: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/rss.xml
Fanpage: https://www.facebook.com/61596507422819/

## Mục tiêu
Tự lấy các bài ẩm thực đã biên tập, được duyệt và công khai trên website, sau đó chia bài cho Buffer và Metricool theo lịch riêng. Không đăng nội dung chưa duyệt, không lẫn với PC GIÁ TỐT.

## Lịch thử nghiệm đề xuất
- 09:30: Metricool, bài địa phương/kinh nghiệm chọn món (chỉ khi brand ẩm thực đã kết nối).
- 18:30: Buffer, bài ẩm thực mới từ RSS (chỉ khi kênh Facebook ẩm thực và API đã xác thực).
- Tối đa 2 bài/ngày trong giai đoạn đầu; nếu kênh nào chưa kết nối, để trống, không tăng dồn kênh còn lại.
- Nếu dùng Metricool/Buffer luân phiên cho cùng một nguồn bài, bản ghi mỗi bài chỉ có **một publisher**.

## Chống trùng và an toàn
- Dùng canonical URL, article id, content hash, Facebook Page ID để khóa trùng xuyên hai công cụ.
- Kiểm tra cả Queue/Sent của Buffer, Scheduled/Published của Metricool và lịch sử nguồn trước khi ghi.
- Chỉ lấy từ RSS công khai, không đưa 2.000 ý tưởng/nháp chưa đủ tiêu chí lên Facebook.
- Không gán địa chỉ, số điện thoại, giá, ưu đãi, chỗ đỗ xe... chưa được xác minh.
- Không có token nào trong repo; GitHub Actions dùng Secret riêng dự án ẩm thực.

## Tình trạng
- GitHub có scripts/food_buffer_rss.py và .github/workflows/food-buffer-rss.yml, mặc định **không gửi bài** khi chưa có khóa Buffer + ID kênh ẩm thực + cờ enable.
- Metricool tài khoản được kết nối hiện chỉ hiện thương hiệu PC GIÁ TỐT (brand 8097086); **chưa có brand ẩm thực**, do đó chưa thể lên lịch cho Fanpage Ăn Ngon Có Deal qua Metricool.
- Chưa xác nhận API Buffer và queue ẩm thực chạy thành công; cần thử một bài với URL Facebook trước khi xem là hoàn tất.
