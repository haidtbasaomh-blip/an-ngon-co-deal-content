# ĂN NGON CÓ DEAL — Repo nội dung (độc lập PC GIÁ TỐT)

Repo này chứa hàng đợi **37 bài biên tập mới** (`data/queue.json`), danh sách **51 bài hiện có** để chống trùng (`data/existing_ids.json`), công cụ kiểm tra Python và bộ cầu nối Cloudflare tùy chọn.

**Quan trọng:** Nội dung ở GitHub là **dữ liệu chuẩn bị** (`ready_for_site`), CHƯA đồng nghĩa đã được xuất bản tại `https://an-ngon-co-deal.bvthn-1903.chatgpt.site/`. Không sử dụng mã nguồn hoặc secrets của PC GIÁ TỐT.

## Vận hành tự động GitHub Actions (miễn phí theo hạn mức GitHub)

Workflow `Food editorial staging` chạy khi nguồn thay đổi và theo lịch 07:17/19:17 Hà Nội. Nó kiểm thử và bổ sung tối đa 100 bài đã biên tập/được duyệt vào `out/ready.json`, chống trùng với 51 bài cũ và dữ liệu đã xuất. Nó không tự sáng tác các bài mới: cần bổ sung bài gốc thật vào hàng đợi trước.

Để chạy tại máy tính: `python -m unittest discover -s tests -v` và `python scripts/pipeline.py --batch-size 100`.

## Bước kết nối với website chính

ChatGPT Sites hiện chưa cấp quyền API ghi từ repo. Khi quyền `Edit` có lại, mở đúng Site ĂN NGON CÓ DEAL và dùng hướng dẫn `SITE_EDITOR_ONE_TIME.txt` để Site đọc nguồn `https://raw.githubusercontent.com/haidtbasaomh-blip/an-ngon-co-deal-content/main/out/ready.json`. Từ chối thêm bài nếu không kiểm tra nguồn và thiếu trường `approved`/`editorialStatus`, tránh trùng ID, kiểm tra metadata, RSS, sitemap và bài trả HTTP 200.

**Chưa kết nối:** Lazada Affiliate, đăng Fanpage, API Cron Cloudflare; không tự hứa số hoa hồng hoặc số bài xuất bản công khai.

## Bảo mật

Repo Public chỉ chứa nội dung có thể công khai. Không đưa API tokens, mật khẩu, khóa ký số, tên/điện thoại cá nhân không công khai vào repo. Cầu nối Cloudflare chỉ đọc và cần triển khai riêng nếu muốn dùng.