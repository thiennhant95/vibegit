# 🧪 vibegit

**Repo của bạn bao nhiêu phần trăm là "AI slop"?** Một lệnh, hai giây, biết ngay.

`vibegit` đọc lịch sử git (chỉ metadata commit, **không đọc nội dung file**, không gọi mạng) và trả về:

- **Slop score 0–100** — càng cao càng nhiều dấu hiệu code ẩu/AI hoá vội
- **Ước lượng AI-assisted** — % commit có dấu hiệu AI, tách rõ *confirmed* (trailer/author) và *likely* (message)
- **Top tín hiệu**: commit khổng lồ, message cụt, xoá test, file bị sửa liên tục, commit chỉ đụng lockfile
- **Badge SVG** để dán vào README + một dòng `--share` để đăng X/Bluesky

Zero dependency. Chỉ cần Python 3.8+ và `git`.

```
+-- vibegit ----------------------------------------------------
| repo      my-app (main)
| commits   412
| slop      38/100  Slop
| AI-assist ~41.5%  (confirmed 12.3% / likely 29.2%, high confidence)
+-- top signals ----------------------------------------------
| AI assistance    20.8 pts
| giant commits    18% (74) -> 4.5 pts
| short messages   22.6% (93) -> 5.7 pts
| test deletions   3 commits -> 12.0 pts
| file churn       7.2% of files (>5 edits) -> 3.6 pts
| lockfile-only    4 commits -> 4.0 pts
+-- AI tools -------------------------------------------------
| claude x51, cursor x9
+-- share ----------------------------------------------------
| vibegit · my-app: slop 38/100 (Slop) · AI-assisted ~41.5%
+--------------------------------------------------------------
```

## Vì sao?

Vibe coding đã thắng. Nhưng "repo này có bao nhiêu phần là máy viết, và nó có ẩu không?" thì chưa ai trả lời được. `vibegit` trả lời bằng dữ liệu có sẵn: git history.

Nó không đoán mò nội dung. Nó nhìn vào thứ AI để lại: trailer `Co-Authored-By`, author bot/AI, message "Generated with …", commit 600 dòng không test, message `wip`, test bị xoá, lockfile bị commit riêng…

## Cài đặt

Không cần cài. Copy `vibegit.py` vào máy, hoặc:

```bash
git clone https://github.com/thiennhant95/vibegit && cd vibegit
python3 vibegit.py --help
```

## Dùng

```bash
python3 vibegit.py .                          # card tổng quan
python3 vibegit.py . --format md > report.md  # Markdown (PR comment)
python3 vibegit.py . --format json            # JSON cho tool khác
python3 vibegit.py . --badge vibegit.svg      # badge cho README
python3 vibegit.py . --share                  # 1 dòng để đăng mạng xã hội
python3 vibegit.py . --since "90 days ago"    # chỉ 90 ngày gần nhất
python3 vibegit.py . --max-score 40           # CI gate: fail nếu slop > 40
```

**Exit codes:** `0` ok · `1` vượt `--max-score` · `2` không phải git repo / không có commit · `4` lỗi git.

## Cách tính điểm

| Tín hiệu | Trọng số tối đa | Ghi chú |
|---|---|---|
| AI assistance | 30 | `confirmed% + 0.5 × likely%`, cap 60% |
| Giant commits | 10 | commit > 400 dòng thay đổi |
| Short messages | 10 | subject < 15 ký tự hoặc `wip/fix/update/...` |
| Test deletions | 20 | commit xoá file test mà không thêm gì |
| File churn | 15 | % file bị sửa > 5 lần |
| Lockfile-only | 15 | commit chỉ đụng lockfile |

Verdict: `0–14` Clean · `15–34` Mild slop · `35–59` Slop · `60+` Heavy slop.

**Confirmed** = trailer `Co-Authored-By` / `Assisted-by` / `Generated-by` có tên AI, author/committer là bot AI, hoặc message "Generated with [tool]".
**Likely** = message/trailer nhắc tới AI tool nhưng không đủ chắc.

Con số AI-assisted là **ước lượng có dải tin cậy**, không phải bằng chứng tác giả. Repo ít commit (<15) sẽ ghi confidence thấp.

## Badge

```markdown
![vibegit](vibegit.svg)
```

Màu đổi theo verdict: xanh (Clean) → vàng (Mild) → cam (Slop) → đỏ (Heavy).

## CI

```yaml
- name: vibegit
  run: python3 vibegit.py . --max-score 40 --format md > vibegit.md
- uses: actions/upload-artifact@v4
  with: {name: vibegit-report, path: vibegit.md}
```

Xem `examples/github-action.yml`.

## Quyền riêng tư

- Chỉ chạy `git log` / `git rev-parse` (read-only).
- **Không đọc nội dung file**, không đọc secret, không gọi mạng, không upload gì.
- Không thực thi nội dung repo.

## Giới hạn (nói thật)

- Là **heuristic**, không phát hiện được AI viết không để lại dấu vết (không trailer, không bot, message bình thường).
- Không đánh giá đúng/sai thuật toán; chỉ đo dấu hiệu quy trình.
- Shallow clone (`--depth 1`) chỉ thấy 1 commit — dùng full clone để có kết quả đầy đủ.
- Chỉ số churn/lockfile có thể cao ở repo lớn nhiều năm; dùng `--since` để so sánh công bằng.

## Roadmap

- [ ] `--compare` hai khoảng thời gian (trước/sau khi dùng AI)
- [ ] `--leaderboard DIR` xếp hạng nhiều repo
- [ ] phát hiện "test bị vô hiệu hoá" (skip/xfail tăng)
- [ ] ước lượng thời gian tiết kiệm/độ rủi ro theo ngôn ngữ

License MIT.
