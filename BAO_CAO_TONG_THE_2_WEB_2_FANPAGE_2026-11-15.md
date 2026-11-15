# BÁO CÁO TỔNG THỂ - 2 WEBSITE VÀ 2 FANPAGE
**Mốc đối chiếu:** 15/11/2026 (giờ Hà Nội). **Phân loại:** Tài liệu bàn giao, phục hồi ngữ cảnh dự án. Không phải xác nhận tất cả tích hợp đã hoạt động.

## Mục tiêu cố định của người sử dụng
- Hai dự án tách biệt: **PC GIÁ TỐT** và **Ăn Ngon Có Deal**; mỗi dự án 1 website + 1 Fanpage, không trộn bài/dữ liệu.
- Mỗi website **3 bài mới/ngày**, mỗi Fanpage **3 bài mới/ngày**, tối đa **12 lượt xuất bản/ngày** trên 4 kênh khi đã triển khai đầy đủ; không tự đăng bản nháp hay bù dồn bài.
- Kết nối **2 chiều**: website -> đúng Fanpage theo bài đã duyệt và Facebook -> kho nhận bài của đúng website. Tránh vòng lặp, trùng URL, trùng lịch, trùng chủ đề.
- Đưa **hàng nghìn sản phẩm có Lazada Affiliate hợp lệ** lên website PC GIÁ TỐT; tự cập nhật theo API, hình ảnh đúng, giá có nguồn, phân loại chuẩn. Facebook quảng bá có chọn lọc, không đăng hàng nghìn sản phẩm thành hàng nghìn bài trong ngày.
- Bài gốc viết tiếng Việt, ngắn gọn hữu ích, hình ảnh phù hợp, hấp dẫn; ý tưởng từ VN và thế giới có dẫn nguồn, không sao chép nguyên văn/ảnh chưa có quyền.
- Không nhập hàng/không giữ kho, không quảng cáo trả phí; ưu tiên công cụ miễn phí, tự chạy server-side không cần bật máy; giữ dữ liệu/secret và source đang hoạt động.
- Khi cần thao tác: gửi link đúng nơi, hướng dẫn ngắn gọn theo bước, không đưa người dùng vào nhiều công cụ cùng lúc.

## 1. Danh tính các kênh
| Hạng mục | PC GIÁ TỐT | Ăn Ngon Có Deal |
|---|---|---|
| Website | https://pc-gia-tot.pages.dev/ | https://an-ngon-co-deal.bvthn-1903.chatgpt.site/ |
| Fanpage | https://www.facebook.com/pcgiatotvn/ | https://www.facebook.com/profile.php?id=61596507422819 |
| GitHub | https://github.com/haidtbasaomh-blip/pc-gia-tot | https://github.com/haidtbasaomh-blip/an-ngon-co-deal-content |
| Nhà xuất bản Facebook đang ưu tiên | Metricool brand 8097086 | Zapier RSS -> Buffer channel 6af914e962b70b94b0375e37 |
| Bộ máy website | Cloudflare Pages, Workers, D1 | ChatGPT Sites |
| Tình trạng 2 chiều | CHƯA HOÀN TẤT | CHƯA HOÀN TẤT |

## 2. Tiến độ được kiểm chứng ngày 15/11/2026
**PC GIÁ TỐT**
- Production trả `/api/public/build` phiên bản **7.3.6**, patch `buffer-safe-queue-metricool-dedupe`.
- `/api/public/lazada-status`: **149 sản phẩm published**, kết nối `configured=true`, trạng thái `ok`, chạy đồng bộ đã được quan sát. Chỉ tiêu hàng nghìn sản phẩm chưa đạt; một số bản ghi thiếu ảnh/giá, cần kiểm tra phân loại.
- `/rss.xml` trả **404**: cầu nối tự động lấy bài từ website còn thiếu.
- Metricool: **18 bản ghi trong kỳ kiểm tra**, trong đó **1 đã đăng, 17 chờ**. Gồm bài danh mục Lazada Affiliate lên lịch **12:30 ngày 16/11/2026**, `autoPublish=true`, status `PENDING`. Đây là lịch dự kiến, không phải đã lên Facebook.
- Buffer PC: kênh `6af6b13062b70b94b016735c`, quy trình GitHub đẩy Buffer đang **HOLD** theo quy tắc để không trùng Metricool. Cần xác minh Page ID chính xác trước khi thay đổi.
- Repo GitHub hiện chủ yếu chứa chương trình giám sát và đồng bộ phụ trợ. ZIP source V7.1.9 đã có trong Library, **cũ hơn bản 7.3.6 live**, không được upload đè.
- Mảng Affiliate tiếp theo: ưu tiên Lazada; Shopee/Tiki/Amazon và các sàn khác chỉ triển khai khi có API, quyền và chương trình Affiliate hợp lệ.

**Ăn Ngon Có Deal**
- Website có **51 bài cũ + bài Bún riêu mới** (mốc làm việc); bài mới `bun-rieu-ha-noi` công khai, có trong RSS, canonical và ảnh minh họa.
- Kho **2.000 bản nháp** cần giữ riêng; không tự đăng hàng loạt.
- Zapier RSS -> Buffer: ảnh chụp người dùng xác nhận Zap **Successful lúc 10:15:09 ngày 15/11**; Buffer có đúng **1 bài Bún riêu xếp lịch 18:30 cùng ngày**. Chưa có kiểm chứng Facebook `Sent`/URL công khai ở mốc báo cáo.
- Github có workflow chuẩn bị nội dung/kiểm thử; workflow API Buffer trực tiếp trước đó lỗi **HTTP 401**. Đã bổ sung **SAFE HOLD** tránh chạy song song với Zapier; đây không phải lỗi cần mở lại khi Zapier đã phụ trách.
- Metricool hiện chưa có brand ẩm thực trong tài khoản được kiểm tra.
- Trang ẩm thực và Fanpage cần tiếp tục tối ưu ảnh, thông tin địa phương thật, 3 bài/ngày khi đủ nội dung đã duyệt.

## 3. Bốn công cụ: phân công một nhiệm vụ
| Công cụ | PC GIÁ TỐT | Ăn Ngon Có Deal | Quy tắc |
|---|---|---|---|
| **GitHub** | Mã giám sát, chính sách, QA, ghi lịch sử | Chuẩn bị nội dung, QA, RSS staging | Không chứa token; không tự đồng nghĩa đã đăng web |
| **Zapier** | Chưa là nhà xuất bản | Trigger bài RSS mới -> Buffer | Không nhân đôi Zap cùng nguồn |
| **Buffer** | Giữ kết nối, không tự thêm bài khi Metricool là chính | Xếp lịch và đăng bài từ Zapier | Kiểm tra Queue + Sent |
| **Metricool** | Nhà xuất bản chính; giữ lịch hiện có | Chưa nối | Không để Metricool và Buffer đăng cùng bài |
**Kết luận:** Chưa gỡ công cụ vì tài khoản/lịch có thể còn dữ liệu. Tuy nhiên mỗi Fanpage chỉ có **một luồng tự động xuất bản chính** tại một thời điểm.

## 4. Hai chiều: định nghĩa đã xong
**Chiều A - Website -> Facebook:** (1) bài được duyệt và có URL công khai; (2) có canonical và ảnh; (3) ghi `article_id`, `source_site`, `publisher`; (4) chống trùng ở các lịch; (5) gửi đúng kênh; (6) có URL bài Facebook thật sau `Sent/Published`.
**Chiều B - Facebook -> Website:** (1) đọc bài Fanpage chính chủ qua Meta Graph API/webhook theo quyền; (2) phân biệt bài do web đã xuất bản để không vòng lặp; (3) chỉ nhận bài tạo trực tiếp trên Facebook; (4) ghi vào vùng chờ của website; (5) tự xuất bản khi thỏa quy tắc kiểm tra hoặc duyệt; (6) giữ liên kết về post gốc.
**Trạng thái:** A đã thử thành công đến Buffer ở ẩm thực và lên lịch qua Metricool ở PC. B **chưa có quyền Meta Page đọc bài và chưa triển khai cơ chế nhập bài vào cả hai CMS**. Không ghi đã đồng bộ 2 chiều.

## 5. Chống đăng trùng bắt buộc
- Mỗi khóa: `facebook_page_id + canonical_url + article_id + normalized_content_hash`.
- Một URL chỉ dành cho một publisher trên mỗi Fanpage; dự phòng `reserved -> queued -> published`, luôn kiểm tra Queue/Sent/Scheduled/Published trước khi xếp lịch.
- Nếu thất bại: ghi lỗi, không tự tạo bài mới liên tục; không bù dồn bài.
- Facebook -> website: nếu đã có `origin_website_article_id` hoặc canonical của website, chỉ cập nhật liên kết/trạng thái chứ không tạo bài mới.
- Giữ mức 3 bài/ngày/website và 3 bài/ngày/Fanpage, không vượt số lượng chỉ để đạt KPI.
- Đã lưu chính sách mỗi dự án ở `config/social_publishing_policy.json`. Script GitHub trực tiếp PC và ẩm thực đã bổ sung chặn an toàn; **chưa có khóa phân tán xuyên cả 4 nền tảng đang chạy thực tế**.

## 6. Nguồn nội dung & thương mại
**Nguồn tham khảo có cấu hình:** PC: Tinh tế, Thanh Niên (thủ thuật/sản phẩm), Tom's Hardware. Ẩm thực: Thanh Niên (ẩm thực), Ngôi Sao và The Guardian Food. Workflow GitHub thu **tiêu đề và URL ý tưởng**, không tự sao chép hay xuất bản.
**PC GIÁ TỐT:** Bách khoa CNTT A-Z, thiết bị, phần mềm, network/security, Windows/driver, bảo mật, AI, cloud, IT bệnh viện, hướng dẫn có ảnh/đánh dấu vị trí, so sánh và lựa chọn mua. Link Lazada phải lấy từ bản ghi thực có `has_lazada` và `/go/{id}`, tránh công khai token, không cam kết giá/hoa hồng khi chưa xác thực.
**Ăn Ngon Có Deal:** món/quán, vùng miền, địa chỉ/đỗ xe/khung cảnh/giá/giờ bán được xác minh, mẹo đặt món, đặc sản, trải nghiệm; chỉ liên kết Affiliate phù hợp ẩm thực và đúng gian hàng.

## 7. Vấn đề còn tồn tại theo ưu tiên
**P0:** Xác thực đúng Page ID trên cả Buffer/Metricool; không gỡ lịch; không bật nhà xuất bản thứ hai. Đảm bảo Facebook ẩm thực Bún riêu thực sự xuất bản sau 18:30 và có URL.
**P0:** Xây quyền Meta Graph API đọc bài Fanpage + tuyến ghi an toàn vào website. Không yêu cầu người dùng đưa token vào chat.
**P1:** Bổ sung RSS nguồn bài đã duyệt trên PC GIÁ TỐT và khả năng tự xuất bản ở đúng website; thiếu full source V7.3.6 khiến chưa thể thay đổi production an toàn.
**P1:** Khảo sát/kiểm định 149 sản phẩm hiện có; phân loại sai, ảnh giả/thiếu, giá null, URL 404; ưu tiên hoàn thiện pipeline Lazada API và tốc độ tăng hàng nghìn sản phẩm hợp lệ.
**P1:** Với website ẩm thực, kiểm tra quyền biên tập ChatGPT Sites, quy trình đăng 3 bài đã duyệt/ngày, không đụng 2.000 bản nháp.
**P2:** Đo lường nhấp link Affiliate, lỗi 404, hiệu quả Facebook; kết nối Shopee/Tiki/Amazon khi đủ phê duyệt và điều kiện kỹ thuật.

## 8. Chuẩn nghiệm thu
- 1 bài mới từ website PC -> Metricool -> Facebook URL công khai, không trùng bài đã hẹn.
- 1 bài mới từ website ẩm thực -> RSS -> Zapier -> Buffer -> Facebook URL công khai, không lặp.
- 1 bài được đăng trực tiếp trên mỗi Fanpage -> về đúng CMS -> một bản ghi chờ/đã duyệt, không tự phát lại Facebook.
- Mỗi website và Fanpage duy trì tối đa 3 bài/ngày và đúng mốc nội dung.
- Lazada: ghi `total imported`, `published`, tỷ lệ có ảnh thật, giá hợp lệ, danh mục đúng, link Affiliate mở đúng sàn; mục tiêu >=1.000 sản phẩm đạt tiêu chuẩn, chưa đạt ở mốc báo cáo.
- Tất cả log riêng, token nằm trong secret, không lộ, giữ nguyên dữ liệu cũ và kế hoạch đăng.

## 9. Đường dẫn vận hành
- PC website: https://pc-gia-tot.pages.dev/
- PC Affiliate: https://pc-gia-tot.pages.dev/san-pham-moi/
- PC Lazada status: https://pc-gia-tot.pages.dev/api/public/lazada-status
- PC build: https://pc-gia-tot.pages.dev/api/public/build
- PC GitHub: https://github.com/haidtbasaomh-blip/pc-gia-tot
- PC Metricool: https://app.metricool.com/planner/calendar?blogId=8097086
- Ẩm thực website: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/
- Ẩm thực RSS: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/rss.xml
- Ẩm thực GitHub: https://github.com/haidtbasaomh-blip/an-ngon-co-deal-content
- Ẩm thực Buffer: https://publish.buffer.com/channels/6af914e962b70b94b0375e37/schedule
- Zapier History: https://zapier.com/app/history
- Trạng thái và các con số chỉ đúng tại thời điểm kiểm tra; phải đối chiếu lại trước khi triển khai.

## 10. Để tiếp tục cuộc trò chuyện sau
“Tiếp tục dự án 2 website + 2 Fanpage theo BAO_CAO_TONG_THE_2_WEB_2_FANPAGE_2026-11-15.md. Không tạo website mới, không xóa dữ liệu/secret/lịch. Ưu tiên xác thực đồng bộ 2 chiều thực tế và Lazada >1.000 sản phẩm chất lượng. Chỉ bật một publisher/Fanpage, tối đa 3 bài/ngày/kênh. Chủ động làm phần kỹ thuật; khi cần quyền truy cập, gửi link và hướng dẫn một bước ngắn gọn.”

## Cập nhật kỹ thuật cùng ngày - thành phần chiều Facebook -> Website
- Đã thêm `scripts/facebook_to_web_candidates.py` cho **cả 2 kho GitHub**. Script chỉ đọc các bài do đúng Fanpage đăng qua Meta Graph API chính thức, loại bỏ các bài đã dẫn từ website để ngăn vòng lặp và xuất file ứng viên **ở máy chạy**, để xét duyệt trước khi đưa lên web.
- Đã thêm `tests/test_facebook_to_web_candidates.py` kiểm tra sai Page ID, bài chưa xuất bản, bài trùng web, chế độ thiếu quyền dừng an toàn; thêm `.gitignore` để không đưa nội dung ứng viên hay dữ liệu token vào GitHub.
- Kiểm thử GitHub của dự án ẩm thực tại mốc cập nhật báo cáo trả **success**. Hai chiều **chưa chạy production**: còn thiếu Page Access Token hợp lệ/quyền đọc Meta, đúng Page ID và API/adapter ghi bài đã duyệt của từng website.
- Không được tự bật job, không dán token vào chat, không tự đẩy sản phẩm/bài viết lên Fanpage hoặc website khi chưa kiểm tra trạng thái trùng và danh mục.
