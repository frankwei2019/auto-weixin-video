---
name: wechat-video-publish
description: 道德经视频号自动运营流水线。从 Obsidian 81 章 markdown → 生成 CSV 计划 → 批量定时发布（每天 6:30/21:00）→ 验证视频号后台 → 采集运营数据（播放/完播率/时长/流量来源）→ 写 CSV。已稳定运行 1-19 章，含 cookie 持久化、React 受控组件兼容、位置清空、AI 标注等所有实战踩坑。适用于道德经/批量短视频/视频号自动运营场景。
version: 3.0.0
metadata:
  author: xiaoma
  category: automation
  project: 道德经视频号自动运营
  keywords:
    - 视频号
    - wechat
    - 自动化
    - Playwright
    - 定时发布
    - 数据采集
    - 道德经
---

# 微信视频号自动运营流水线 Skill

## 核心定位

**完整的自动运营流水线**（v3.0）。端到端：

```
Obsidian 81 章 md  →  生成 CSV 计划  →  批量定时发布  →  视频号后台验证  →  采集运营数据  →  CSV 时间序列
```

整个流程**全自动**：脚本完成视频上传、标题/话题/短标题/合集、封面、声明原创、AI 标注、位置清空、定时发布、视频号后台状态读取、运营数据抓取。用户**不需要**任何手动操作。

## 适用场景

- 道德经 81 章**每天 6:30 + 21:00** 双时段自动定时发布（已稳定 1-19 章）
- 其他短视频需要批量/定时发布到视频号
- 个人号想避免封号又需要批量发
- 视频号运营数据自动采集（播放/完播率/平均时长/流量来源占比）

**不适用**：
- 评论互动（账号风险，刻意不做）
- 直播开播
- 单视频用户画像抓取（视频号无 API）

## 技术架构

### 项目位置

```
C:\Users\28658\WorkBuddy\2026-07-31-13-17-15\auto-weixin-video\   # 主发布脚本
C:\Users\28658\WorkBuddy\2026-07-31-13-17-15\shipinhao-automation\  # CSV + 调度 + Obsidian 解析
D:\myObsidian\03-books\02-Areas\道德经\chapters\                  # 道德经 81 章 md 源
D:\ddj-video\                                                     # 视频源文件 1-81.mp4
```

### 完整流水线（6 个脚本）

| 脚本 | 路径 | 作用 |
|---|---|---|
| `gen_schedule.py` | `shipinhao-automation/` | 读 Obsidian md → 追加 schedule.csv 新行（自动从最后 done +1 天排 6:30/21:00） |
| `get_cookie.py` | `auto-weixin-video/scripts/` | `launch_persistent_context` 登录拿 cookie，自动检测 URL 跳转 |
| `publish.py` | `auto-weixin-video/scripts/` | 单视频**全自动**发布（上传+标题+话题+合集+原创+AI标注+位置清空+封面+定时+发表） |
| `batch_publish.py` | `auto-weixin-video/scripts/` | 批量包装器，读 CSV 调 publish.py 透传所有参数，成功后 CSV status=done |
| `check_schedule.py` | `auto-weixin-video/scripts/` | 验证视频号后台实际状态（截图 + dump 定时列表） |
| `collect_stats.py` | `auto-weixin-video/scripts/` | 抓视频号数据中心"单篇视频"17 列数据 + 写 CSV |
| `manual_login.py` | `auto-weixin-video/scripts/` | 打开视频号助手浏览器保活，老 K 手动验证 |

### publish.py CLI 参数

```
python scripts/publish.py
  -v <video.mp4>            # 必填
  -t <title>                # 必填
  -g "#tag1 #tag2 ..."      # 话题，空格分隔
  -o                        # 原创声明
  --cover <cover.jpg>       # 自定义封面
  --mark-ai                 # AI 标注（"含 AI 生成内容"）
  --no-location             # 位置清空（不显示位置）
  -s "2026-08-09 21:30"     # 定时发布
  --skip-publish            # 调试模式（不真发）
  --manual-finish           # 半自动 fallback
  --keep-browser 300        # 保留浏览器秒数
```

### batch_publish.py CLI

```
python scripts/batch_publish.py
  --ignore-time             # 跳过未来时间过滤（提前上传+定时）
  --max-count N             # 一次跑 N 条
  --no-location             # 透传位置清空
  --manual-finish           # 透传半自动
```

## 完整使用流程

### 0. 准备工作（一次性）

- `D:\myObsidian\03-books\02-Areas\道德经\chapters\` — 81 章 md（已有 frontmatter + 原文 + 白话）
- `D:\ddj-video\1.mp4 ~ 81.mp4` — 视频文件
- `D:\ddj-video\0cover.png` — 通用封面源（道德经书法字 + 红印章）

### 1. 登录拿 cookie

```bash
python auto-weixin-video/scripts/get_cookie.py
```
- 浏览器自动最大化弹出
- 微信扫二维码
- 自动检测登录成功（URL 跳到 `post/list`），保存到 `browser_data/` 和 `cookies/weixin_video.json`
- 不用点 Resume（`page.pause()` 不稳定）

### 2. 生成发布计划

```bash
python shipinhao-automation/gen_schedule.py 16 19   # 生成 16-19 章
python shipinhao-automation/gen_schedule.py 20 30   # 生成 20-30 章
```
- 自动读 Obsidian md → 解析 frontmatter/title/原文/白话
- 自动从最后一条 done 的 scheduled_at + 1 天开始
- 节奏：每天 6:30 + 21:00
- 默认生成 pending 状态行

### 3. 批量定时发布

```bash
python auto-weixin-video/scripts/batch_publish.py --ignore-time --max-count 4 --no-location
```
- 读 CSV pending 行
- 调 publish.py 全自动跑（一次性完成所有步骤）
- 跑完一个 mark done，CSV status=done
- 用 `--ignore-time` 提前上传+定时发布（跳过"未来时间过滤"）

### 4. 验证视频号后台

```bash
python auto-weixin-video/scripts/check_schedule.py
```
- 打开视频号"内容管理 > 视频"
- 截图 + dump 14-15 章定时状态

### 5. 采集运营数据

```bash
python auto-weixin-video/scripts/collect_stats.py --days 30
```
- 抓"数据中心 > 视频数据 > 单篇视频" tab
- 17 列：视频/发布时间/完播率/平均时长/播放/点赞/喜欢/评论/关注/分享/...
- 写 `data/stats/YYYY-MM-DD_days{N}.csv`
- **限制**：账号太新时"流量来源占比"图表不渲染（视频号限制）

## Cookie 持久化（关键！）

### 双层防护

- **Layer 1: `launch_persistent_context`** — 整个浏览器状态写到 `browser_data/`，包括 localStorage / cookie / IndexedDB
- **Layer 2: `storage_state` 导出** — 到 `cookies/weixin_video.json`（publish.py 历史用法，但 cookie 只有 2 个不够用）

### publish.py 必须用 launch_persistent_context

**v3.0 关键修复**：

```python
# ✅ 正确：共享 browser_data session
context = await p.chromium.launch_persistent_context(
    user_data_dir=str(BROWSER_DATA_DIR),
    headless=self.headless,
    no_viewport=True,
)
page = context.pages[0] if context.pages else await context.new_page()

# ❌ 错误：临时浏览器 + storage_state 只有 2 cookie
browser = await p.chromium.launch(headless=self.headless)
context = await browser.new_context(storage_state=str(COOKIE_FILE))  # 失败！
```

**storage_state 只有 2 个 cookie（wxb_id + wxb_token）**，视频号识别为未登录，发布时跳 login.html。

**`launch_persistent_context` + browser_data** 才能用上完整的 session。

### 失效场景 + 恢复

- 系统重启 → 一般能续期（browser_data 持久化）
- cookie 失效（1-2 周） → 重跑 `get_cookie.py` 扫码
- 系统更新 → 重跑 `get_cookie.py`

## 关键决策与坑（必读）

### 踩过的坑（按时间倒序）

#### v3.0 (2026-08-27) — Cookie 失效

1. **storage_state 只有 2 个 cookie 不够** — `chromium.launch + new_context(storage_state)` 被视频号识别为未登录。改用 `launch_persistent_context + browser_data`。

#### v2.x (2026-08-01) — 定时 / 位置 / React 受控

2. **React setter 写时间失效** — `Object.getOwnPropertyDescriptor(HTMLInputElement, 'value').set + dispatchEvent('input')` 改了 DOM value 但 React 18 onChange 没同步，提交时 fallback 到默认时间。**改用 Playwright 真点击 input + keyboard.type 输入 HH:MM + Tab blur**。
3. **frame 没有 keyboard 属性** — 必须用 `page.keyboard`，不能用 `target.keyboard`（iframe 无独立键盘）。
5. **月份切换后 stale locator** — React 重渲染让 `target.locator(...)` 引用失效，改用 `target.evaluate("document.querySelector(...)")` 重新查。
6. **时间 picker input 不在 picker 容器下** — 用全局 `input[placeholder="请选择时间"]` 而非 `.weui-desktop-picker input[placeholder="请选择时间"]`。
7. **月份切换按钮 class** — 用 `.weui-desktop-picker__panel__hd .weui-desktop-btn__icon__right`（旧 `.weui-desktop-picker__next` 失效）。
8. **位置字段 class 是 `div.label` 不是 `form-item__label`** — 之前 selector 找不到。
9. **位置清空方法** — 点 `.position-display-wrap` 弹 dropdown → 找 `.option-item .name="不显示位置"` 点击。
10. **iframe 穿透** — 视频号发布页是 iframe `micro/content/post/create`，用 `target = next((f for f in page.frames if "micro/content/post/create" in f.url), page)`。
11. **弹窗在主 frame 不在 iframe** — 原创权益弹窗用 `page.locator(...)`，AI标注可能在 Shadow DOM 需 `frame.evaluate` 递归穿透。

#### v2.0 (2026-07-31) — 原创 / AI标注

12. **`networkidle` 永远等不到** — 视频号页面一直有心跳/统计请求，必须用 `wait_until="domcontentloaded"` + 手动等 iframe。
13. **封面按钮必须在视频上传完后才出现** — `div[class*="cover"]:has-text("编辑")`，不能在视频上传前调。
14. **封面确认按钮 = "确认"，不是"完成/确定/保存"** — 看截图才知道。
15. **React 受控组件需要 Playwright 真点击 `.ant-checkbox-wrapper`** — JS `.click()` 只更新 DOM 不触发 React 状态更新。
16. **AI标注勾选成功 className 是 `mark-tag-option is-selected`** — 探测要看 `is-selected` / `active`。
17. **AI标注必须先展开"视频标注"折叠区** — 直接点 `.mark-tag-option` 找不到。
18. **CSV 话题分隔符** — 用空格分隔，代码不重复加 `#`。

#### v1.0 (2026-07-30) — 基础

19. **`page.pause()` 不靠谱** — 远程桌面下 Playwright Inspector 窗口可能被挡住，扫码后忘了点 Resume → 卡死。改用自动检测 URL/元素跳转。
20. **视频号默认时间会变** — 历史默认是 21:00 → 09:00 → 01:00，所以脚本必须真正写入（不是 React setter 写完就算了）。

### 关键 selector 实测（2026-08-01 起稳定）

```python
# 视频上传
target = next((f for f in page.frames if "micro/content/post/create" in f.url), page)
file_input = target.locator('input[type="file"]')

# 封面按钮（必须视频上传完后才能找到）
await target.locator('div[class*="cover"]:has-text("编辑")').click()

# 封面确认按钮
await target.locator('button:has-text("确认")').click()

# 原创声明（用 JS 找最近 form-item 下的 ant-checkbox）
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
setter.call(checkbox, true);
checkbox.dispatchEvent(new Event('click', {bubbles: true}));

# 原创权益弹窗（在 page 不在 iframe）
await page.locator('.weui-desktop-dialog:has-text("原创权益")').locator('.ant-checkbox-wrapper').click()

# AI标注（展开折叠区后）
await target.locator('text=视频标注').click()  # 展开
await target.locator('.mark-tag-option:has-text("含AI生成内容")').click()

# 定时控件（全部在 iframe）
await target.locator('span.weui-desktop-form__check-content:has-text("定时")').click()
await target.locator('input[placeholder="请选择发表时间"]').click()  # 弹日期 picker
await target.locator('.weui-desktop-picker__panel__hd .weui-desktop-btn__icon__right').click()  # 切月
# 用 JS evaluate 点日期 a 标签（避免 stale locator）
await target.evaluate("""
  () => {
    const links = document.querySelectorAll('.weui-desktop-picker__table a');
    for (const a of links) {
      if (a.innerText.trim() === '27' && !a.className.includes('disabled')) {
        a.click();
        return true;
      }
    }
  }
""")
# 时间（用 page.keyboard 真输入）
await page.keyboard.press('Control+A')
await page.keyboard.press('Delete')
await page.keyboard.type('21:30', delay=120)
await page.keyboard.press('Tab')  # blur

# 位置清空（点 .position-display-wrap 弹 dropdown）
await target.locator('.position-display-wrap').click()
await target.locator('.option-item:has(.name:has-text("不显示位置"))').click()
```

## CSV 格式

`shipinhao-automation/schedule.csv`:

```csv
video_file,title,description,topics,scheduled_at,duration_sec,status,published_at,note
16.mp4,第16章 使我挈有知,"原文 + 白话","#帛书版道德经 #正能量 #经典阅读 #国学",2026-08-27 06:30,,pending,,
17.mp4,第17章 善建者不拔,...,"...",2026-08-27 21:00,,pending,,
```

字段说明：
- `video_file` — 视频文件名（数字开头，如 `16.mp4`）
- `title` — "第N章 章名"
- `description` — 道德经原文 + 白话对照（Obsidian md 解析）
- `topics` — 空格分隔的 hashtag
- `scheduled_at` — 定时发布时间，格式 `YYYY-MM-DD HH:MM`
- `status` — `pending` / `done` / `failed`
- `published_at` — 实际跑过的日期
- `note` — 备注

## 数据采集 CSV 格式

`auto-weixin-video/data/stats/YYYY-MM-DD_days{N}.csv`:

```csv
collect_date,days_window,chapter,publish_date,plays,likes,likes_v2,comments,follows,shares,
forward_ch_chat,set_ringtone,set_status,set_cover,link_clicks_total,link_clicks_unique,
add_to_contacts_total,add_to_contacts_unique,
completion_rate_pct,avg_play_sec,
source_follow_pct,source_friend_pct,source_recommend_pct,
source_share_pct,source_msg_pct,source_page_pct,source_other_pct
```

**已知限制**：
- 流量来源占比：新账号没数据时图表不渲染（视频号限制），账号积累到一定流量后才会显示
- 用户画像 / 单视频详情 / 完播率分时段：视频号后台无 API，抓不到

## 维护清单

- [ ] 视频号 UI 选择器变了 → 更新 `publish.py` 里的 selector
- [ ] cookie 失效 → 重跑 `get_cookie.py`（一般 1-2 周一次）
- [ ] 视频号加了新字段（如新标签）→ 在 `_mark_ai_content` 找新 selector
- [ ] 封面确认按钮文字改了 → 更新 `_upload_cover` 的 close_selectors
- [ ] 弹窗文字/按钮改了 → 更新 `_declare_original` 的 selector
- [ ] React setter 写时间失效 → 检查是否要改回 Playwright keyboard.type

## 关联文件

- `D:\myObsidian\03-books\02-Areas\道德经\chapters\` — 道德经 81 章 .md 源文件
- `D:\ddj-video\` — 视频源文件（`1.mp4` ~ `81.mp4`）
- `D:\ddj-video\0cover.png` — 通用封面源（道德经书法字 + 红印章）
- `shipinhao-automation/scripts/utils.py` — `generate_cover()` 生成 9:16 封面（中国红编号 01-81）
- `auto-weixin-video/data/stats/` — 运营数据 CSV 时间序列

## 输出尺寸与样式（封面）

- **尺寸 1080x1920 (9:16)** — 视频号主流竖屏规格（4:5 被视频号忽略）
- 字号 = 图片高 × 7.5%（"道德经"的 1/4）
- 颜色 = `#C8102E` 中国红
- 位置 = 道德经正下方居中，y = height × 0.42 + font_size/3
- **不要背景框、不要描边**，纯中国红字

## GitHub 仓库

`https://github.com/frankwei2019/auto-weixin-video`

推送时 HTTPS 443 在用户网络被封，**用 SSH**：
```bash
git remote set-url origin git@github.com:frankwei2019/auto-weixin-video.git
git push origin main
```