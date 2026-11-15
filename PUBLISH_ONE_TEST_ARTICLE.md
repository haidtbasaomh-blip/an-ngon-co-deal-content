# Bài thử kết nối website → RSS → Zapier → Buffer → Facebook

**Trạng thái cập nhật 15/11/2026:** **ĐÃ XUẤT BẢN TRÊN SITE** lúc khoảng 10:12 giờ Việt Nam; bài `bun-rieu-ha-noi` đã nằm trong RSS và sitemap công khai. **Chưa xác nhận Zapier → Buffer → Facebook đã đăng.**

Đây là bài có sẵn trong hàng đợi đã duyệt. Không tạo bài giả hoặc bài trùng để thử. Đúng website: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/ (Site ID appgprj_6af7dc2735f4819199c24aded5106f37).
Không sửa PC GIÁ TỐT, không xóa 51 bài cũ, không chạy lại các bài mẫu của Zapier.

## Bài chọn thử

- ID: `bun-rieu-ha-noi`
- Tiêu đề: **Bún riêu Hà Nội: chọn vị thanh hay đậm ngay từ đầu**
- Nhóm: Món Hà Nội / Hà Nội
- Trạng thái nguồn: approved=true; editorialStatus=approved; publicationStatus=ready_for_site
- URL khi được Site xuất bản, **không coi là URL đã hoạt động**: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/bai-viet/bun-rieu-ha-noi/
- Minh họa tự tạo: https://raw.githubusercontent.com/haidtbasaomh-blip/an-ngon-co-deal-content/main/assets/illustrations/bun-rieu-ha-noi.svg
- Link tham khảo: https://dantri.com.vn/du-lich/khach-my-nghien-mot-mon-an-o-ha-noi-san-sang-di-ca-tieng-de-thuong-thuc-20250826211447469.htm
- Không khẳng định địa chỉ, giá, chỗ đỗ xe hoặc ưu đãi quán cụ thể.

### Nội dung đã biên tập

Bún riêu có nhiều phiên bản. Chọn đúng bát mình thích bắt đầu từ cách hỏi nước dùng, riêu và phần ăn kèm.

Bún riêu là một lựa chọn đáng thử khi muốn đổi vị khỏi các món phở quen thuộc. Có người thích bát nước dùng chua nhẹ với cà chua; người khác quan tâm nhiều hơn tới phần riêu và các món thêm. Không nên nghĩ rằng tất cả quán bún riêu đều có một công thức giống nhau.

Trước khi gọi, nhìn thực đơn để phân biệt suất cơ bản với suất có thêm đậu, giò hoặc nguyên liệu khác. Nếu quán bán nhiều loại bún riêu, hỏi xem phần nào đã gồm trong giá. Cách hỏi này hữu ích hơn việc chỉ xem ảnh một bát thật đầy trên mạng.

Người không quen vị mắm hoặc muốn điều chỉnh độ cay có thể đề nghị để riêng gia vị, nhưng phải hỏi quán có hỗ trợ không. Với món mang về, nên để riêng rau và nước nếu người bán cho phép để giữ cách ăn mình muốn.

Bài này giúp lựa chọn kiểu món, không giới thiệu một địa chỉ cụ thể. Giờ bán, giá từng suất và nguồn nguyên liệu luôn cần kiểm tra trực tiếp tại quán trước khi đặt.

> Bài viết cung cấp mẹo chọn món; thông tin cửa hàng, giá cả và giờ mở cửa phải kiểm chứng từ cơ sở thực tế.

## Quy trình thực thi an toàn

1. Trong công cụ biên tập của **chính Site hiện có**, tạo duy nhất bài `bun-rieu-ha-noi` theo nội dung trên. Nếu Site thiếu quyền sửa, **dừng**, không tạo Site khác hoặc đoán API ghi. Bản GitHub chỉ là staging, không làm RSS thay đổi.
2. Khi Site xác nhận công khai, kiểm tra URL bài HTTP 200, `/api/editorial` có `approved=true` và `publicationStatus=published`, canonical/OG, và URL có trong sitemap và `/rss.xml`. Trước thử: 51 bài, 55 URL sitemap; kiểm tra số thực tế sau thử.
3. Zapier: Zap `386773047` đang bật, RSS trigger `New Item in Feed`, action `Add to Queue` chỉ trên kênh Buffer Ăn Ngon Có Deal `6af914e962b70b94b0375e37`. Không bấm `Test step` lên một bài cũ và không tạo Zap thứ hai.
4. Kiểm tra `https://zapier.com/app/history` thấy một lần chạy thành công của bài mới; `https://publish.buffer.com/channels/6af914e962b70b94b0375e37/schedule` có đúng một Queue mới 18:30 theo múi giờ Asia/Bangkok.
5. Sau giờ đăng, xem `Sent` và liên kết Facebook thật. Không nhận là đã đăng thành công nếu chỉ thấy Queue.
6. Nếu không có RSS item mới, không đẩy đi lại bài cũ; báo rõ phần Site cần mở quyền biên tập. Không tự tăng số lượng để bù lịch.

**Đối chiếu sau khi xuất bản ngày 15/11/2026:** URL `/bai-viet/bun-rieu-ha-noi/` công khai, được ghi nhận trong `/rss.xml` và `/sitemap.xml`; mỗi nguồn có **52 URL bài viết duy nhất** (51 bài cũ + bài thử). RSS đặt bài Bún riêu đầu tiên với ngày xuất bản `Sun, 15 Nov 2026 03:12:29 GMT`. Lần chạy GitHub thử Buffer trước đó bị `401 Unauthorized`; **không dùng lỗi của API GitHub để kết luận Zapier OAuth thất bại**, phải kiểm tra Zap History/Buffer Queue/Facebook URL riêng. Chưa bật đăng song song từ GitHub để chống trùng.
