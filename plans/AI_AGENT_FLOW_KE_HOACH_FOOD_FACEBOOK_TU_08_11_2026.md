# KẾ HOẠCH BỔ SUNG AI AGENT / GOOGLE FLOW — ĂN NGON CÓ DEAL + FANPAGE
**Ngày:** 21/11/2026. **Liên kết kế hoạch tổng thể từ 08/11:** https://github.com/haidtbasaomh-blip/pc-gia-tot/blob/main/plans/KE_HOACH_TONG_HOP_AI_AGENT_FLOW_5_KENH_TU_08_11_2026.md

Đây là bản nhánh chuyên trách ĂN NGON CÓ DEAL. **Chỉ lưu ý tưởng, không tự triển khai site/đăng bài/quảng cáo**.

## Đầu bài cố định
- Site gốc giữ nguyên: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/
- Facebook gốc: https://www.facebook.com/profile.php?id=61596507422819
- Bảo toàn 2.000 nháp, ảnh, logo và dữ liệu; không tự đăng hàng loạt, không thay site PC GIÁ TỐT.
- Kho GitHub là staging/QA, không đồng nghĩa có quyền ghi lên ChatGPT Sites. Trước khi xuất bản phải kiểm tra CMS thực, canonical, RSS, sitemap, ảnh và nguồn.
- Facebook chọn đúng một publisher; hiện theo báo cáo tổng hợp là Buffer, không bật thêm Metricool hoặc Zapier đăng cùng bài.
- Facebook->website đưa bài do Page tạo trực tiếp về vùng chờ biên tập, không tự phát ngược lại Page.

## Các ý tưởng phải bảo lưu từ 08–21/11
1. **Food Local Agent**: kiểm tra tên quán, vị trí, quận/phường, alias Hoàn Kiếm/Hoan Kiem, đúng địa chỉ từng chi nhánh; không bịa giá/giờ/đỗ xe.
2. **Editorial Agent**: series Bún riêu Hà Nội, món theo mùa, món vùng miền, ẩm thực Tây Bắc, mẹo gọi món; mỗi bài gốc riêng và không sao chép review.
3. **Image Rights Agent**: ảnh/quay món ăn thật có quyền sử dụng, rõ nguồn và tác giả; thiếu ảnh thật thì giữ nháp thay vì dùng hình AI giả món tại quán.
4. **SEO Agent**: kiểm tra robots/noindex cho bài công khai, bảo vệ nháp, RSS chỉ bài đã duyệt, sitemap/canonical/OG/JSON-LD cho bài/quán, mobile, tìm kiếm đúng địa chỉ.
5. **FB Bridge Agent**: từ bài web đã duyệt sang đúng Fanpage, chống trùng URL/ID/hash; từ bài Fanpage về đúng kho nháp trên web với source FB ID.
6. **Affiliate Agent**: tìm chương trình hợp lệ cho thực phẩm/dụng cụ bếp khi tài khoản và media đã được duyệt; nguồn/link chính xác, không tự thêm SKU PC.
7. **Audience Insights**: xem bình luận và câu hỏi thực tế làm ý tưởng mới (không thu thập PII); đo lượt xem, click và tương tác có chứng cứ, không nhầm bài staging với doanh thu.
8. **Flow Visual Assistant**: có thể thử minh họa về văn hóa ẩm thực trừu tượng, transition hoặc đồ họa mở bài, nhưng **không** dùng clip AI như footage quán/món ăn thật; không bật API trả phí.

## Tiến độ và kiểm duyệt
- Mốc 14/11: 51 bài cũ, 37 staging và 2.000 nháp là các mốc lịch sử khác loại.
- Mốc checkpoint 21/11: báo cáo đối chiếu 53 bài công khai, ANW-15 và ANW-17 được nghiệm thu theo từng mã; không khẳng định tất cả giấy phép ảnh đã đủ.
- Không nâng số mục 117 khi chỉ thêm file này.
- Giữ một nguồn phát hành chính; không gửi bài khi không có URL public, consent cần thiết hoặc quyền Meta; không lấy secrets ra khỏi hệ thống.

## Thứ tự xử lý
P0 bảo toàn dữ liệu và nháp -> P1 ảnh/địa chỉ/SEO/RSS -> P2 một bài đã duyệt web->Facebook có URL post thật -> P3 Page->website một bản nháp an toàn -> P4 sản xuất chuỗi nội dung mới -> P5 thử AI Agent/Flow sau khi kiểm duyệt.

**Tiêu chí xong:** có URL bài công khai và nguồn ảnh/địa điểm; bài Facebook cùng một Page ID có URL thực; đường Facebook->web chỉ lưu nháp và có chống vòng lặp. Không xóa hoặc tự động xuất bản phần chưa được duyệt.
