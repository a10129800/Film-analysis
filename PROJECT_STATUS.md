> 本文件是 ShotBreakdownAssistant 的目前專案狀態摘要。
> 修改程式前，請先閱讀本文件。
> 不要假設歷史版本與目前程式碼相同。
> 如果不確定目前狀態，應先檢查實際檔案，而不是自行推測。

# ShotBreakdownAssistant 專案狀態

最後依實際檔案盤點：2026-08-17。此文件描述的是工作樹目前狀態，不代表所有內容都已提交或已封版。

## 1. 專案目前版本

- **目前版本名稱：** `🎬 拉片助手 v1.2`（`main.py` 的 `APP_NAME`）。
- **最近一次已標記版本／穩定基準：** Git tag `v1.2.0`，指向 commit `761c3c5`（`Initial working version v12`）；另有對應的 `version/v1.2.0/` 快照資料夾。
- **最新提交：** `ae27f0a`（`refactor: separate application services`，2026-08-16）。此 commit 在 `v1.2.0` tag 之後，尚未有新 tag。
- **目前工作樹：** 非乾淨狀態。`main.py`、`services/video_service.py` 已修改；`controllers/`、`widgets/`、`core/project_state.py` 尚未被 Git 追蹤。這些內容包含近期的模組化工作。
- **最近一次修改內容：** 將播放控制接到 `PlaybackController`、抽出 `ThumbnailTimeline`、`ShotPanel`、`VideoPanel`，並新增 `ProjectState`／`ProjectController`；`services/video_service.py` 另有未提交的 OpenCV 取影格方法。

## 2. 專案結構

主要結構如下（略過 `build/`、`dist/`、`__pycache__/` 等產物）：

| 路徑 | 用途 |
| --- | --- |
| `main.py` | PySide6 應用程式入口與主視窗協調層。 |
| `core/time.py` | 毫秒格式化為時間字串。 |
| `core/shot.py` | `Shot` 資料模型與序列化。 |
| `core/project.py` | JSON 專案檔的底層讀寫。 |
| `core/project_state.py` | 目前專案的記憶體狀態 dataclass（未追蹤）。 |
| `services/video_service.py` | 尋找 FFmpeg/FFprobe、呼叫 FFmpeg 產生縮圖；另有未提交的 OpenCV 取影格方法。 |
| `services/thumbnail_service.py` | 決定縮圖目錄、建立目錄、清除 JPG。 |
| `services/project_service.py` | 封裝 `core/project.py`，載入時還原 `Shot` 物件。 |
| `services/shot_service.py` | 新增、排序、刪除與更新 Shot。 |
| `services/obsidian_service.py` | 由影片與 Shot 產生 Obsidian Markdown。 |
| `controllers/playback_controller.py` | Qt 播放、倒播、速度及相對跳轉控制（未追蹤）。 |
| `controllers/project_controller.py` | 專案新建、開啟、載入、儲存、匯出的非 UI 協調層（未追蹤）。 |
| `widgets/video_panel.py` | 影片畫面、播放鍵、時間軸、影片資訊與預覽 UI（未追蹤）。 |
| `widgets/shot_panel.py` | Shot 清單、筆記、景別及相關 UI 訊號（未追蹤）。 |
| `widgets/thumbnail_timeline.py` | 可捲動縮圖時間軸與縮圖點擊訊號（未追蹤）。 |
| `version/v1.2.0/` | v1.2.0 的部分程式快照，不應假定與根目錄目前完整一致。 |
| `ffmpeg/` | Windows 的 `ffmpeg.exe`／`ffprobe.exe`，執行與封裝所需。 |
| `ShotBreakdownAssistant.spec` | PyInstaller Windows 封裝設定。 |

## 3. `main.py`

`ShotBreakdownAssistant(QMainWindow)` 是目前唯一主視窗 class；`main()` 建立 `QApplication` 並顯示視窗。

### 主要責任

- 建立工具列、分割窗格，並組裝 `VideoPanel`、`ShotPanel`、`ThumbnailTimeline`。
- 顯示檔案選擇器、訊息框與縮圖產生進度視窗。
- 協調 `QMediaPlayer`、各 controller／service 與 UI 訊號。
- 執行縮圖生成迴圈、Shot 選取及更新、鍵盤事件處理。

### 主要方法

- 初始化／UI：`__init__`、`setup_shortcuts`、`build_ui`、`setup_player`。
- 播放：`play_backward`、`play_forward`、`increase_playback_speed`、`seek_relative`、`toggle_play`、`seek_video`、`position_changed`、`duration_changed`、`keyPressEvent`。
- 影片與縮圖：`open_video`、`generate_thumbnails`、`clear_thumbnails`、`refresh_thumbnail_timeline`、`thumbnail_clicked`。
- Shot：`refresh_shot_list`、`select_shot`、`set_shot_size`、`note_changed`、`add_current_shot`、`delete_current_shot`。
- 專案：`new_project`、`save_project`、`load_project`、`export_obsidian`。

### 已模組化的功能

- 播放演算法與 timers：`PlaybackController`。
- 專案資料容器：`ProjectState`；存檔／載入／匯出協調：`ProjectController`。
- 影片、Shot、縮圖 UI：各自位於 `widgets/`。
- FFmpeg、縮圖檔案、Shot 資料、專案 JSON、Obsidian 匯出：各自位於 `services/` 或 `core/`。

### 仍集中於 `main.py`

- `generate_thumbnails()` 同時處理前置檢查、進度視窗、取消、逐張 FFmpeg 呼叫、Shot 建立、錯誤顯示與 UI 刷新。
- Qt 檔案對話框、訊息框、狀態列文字與 controller/UI 的接線。
- Shot 資料修改後的面板刷新與目前選取同步。
- `show_preview_frame()` 的 OpenCV BGR→Qt pixmap 轉換。
- `ProjectState` 雖已集中狀態，但 `main.py` 仍以 `video_path`、`shots` 等 property 轉接存取。

## 4. `services/`

| Service | 責任 | `main.py` 的使用方式 |
| --- | --- | --- |
| `video_service.py` | 找 FFmpeg／FFprobe，透過 FFmpeg 產生單張 JPG 縮圖。未提交部分另提供 `open_video`、`close_video`、`get_frame_at`、`get_frame` 的 OpenCV 介面。 | 建立為 `self.video_service`；`generate_thumbnails()` 對每個時間點呼叫 `generate_thumbnail()`。目前 main 沒有呼叫 OpenCV 取影格介面。 |
| `thumbnail_service.py` | 取得 `.shotbreakdown_<影片名>/thumbnails` 目錄、建立目錄、刪除其中 `*.jpg`。 | 建立為 `self.thumbnail_service`；縮圖生成前準備／清空目錄，清除縮圖時再次呼叫。 |
| `project_service.py` | 呼叫 `core.project` 讀寫 JSON，並於讀取後重建 `Shot`。 | 不再由 main 直接建立；由 `ProjectController` 使用。 |
| `shot_service.py` | 新增並依時間排序、刪除 Shot、更新筆記與景別。 | 建立為 `self.shot_service`；縮圖生成、手動新增、刪除、筆記與景別操作均使用它。 |
| `obsidian_service.py` | 將影片、Shot、縮圖名稱、筆記輸出成 Markdown。 | 不再由 main 直接建立；由 `ProjectController` 使用。 |

目前沒有其他已確認的 `services/*.py` 檔案。

## 5. `controllers/`

目前有兩個 controller，兩者都尚未被 Git 追蹤：

- **`PlaybackController`：存在，且確實被 main 使用。** `main.py` 在 `setup_player()` 建立 `self.playback_controller`，將 `QMediaPlayer` 與 `duration_ms` provider 傳入；`J`／`L`、左右跳轉、暫停與新專案流程都會使用它的 timers 或方法。
- **`ProjectController`：存在，且確實被 main 使用。** main 透過它產生新狀態、開影片、讀取／儲存專案及匯出 Obsidian。

## 6. 播放控制（依目前實際程式碼）

| 操作 | 目前行為 |
| --- | --- |
| `J` | `QShortcut` 會呼叫 `play_backward()`；若 `reverse_timer` 已在運行，`keyPressEvent` 會停止它並隱藏預覽。首次倒播時 controller 先暫停 player、回退 200 ms，然後以 150 ms timer 持續將 position 往回設。再次由 controller 呼叫時，速度循環為 1→2→4→8→1。 |
| `K` | `QShortcut` 連到 `toggle_play()`；`keyPressEvent` 也會停止正／倒播 timer、暫停 player、把按鈕改為「播放」，並顯示「已停止播放」。實際效果是停止播放；兩條事件路徑同時存在。 |
| `L` | `QShortcut` 會呼叫 `play_forward()`：停止倒播 timer，播放速度循環為 1→2→4→8→1，設定 `QMediaPlayer` playback rate 後播放。`keyPressEvent` 另會檢查 `forward_timer`；但目前程式沒有呼叫 `forward_timer.start()`，因此正常情況會再呼叫一次 `play_forward()`，此雙重路徑需要實機確認。 |
| 快轉 | `PlaybackController.forward_step()` 有每 50 ms 前進的實作，但沒有被啟動；實際 L 快轉依賴 `QMediaPlayer.setPlaybackRate()`。 |
| 倒播 | 使用 `QElapsedTimer` 計算耗時，搭配 150 ms `reverse_timer` 將 player position 往回設；到 0 ms 自動停止。 |
| 播放速度 | 共用 `playback_speeds = [1.0, 2.0, 4.0, 8.0]`。`play_forward()`／`play_backward()` 都會循環速度。`increase_playback_speed()` 存在但目前沒有看到對應 UI 或快捷鍵連接。 |
| 左右跳轉 | `Left`／`Right` 分別跳 -1000／+1000 ms；`Shift+Left`／`Shift+Right` 分別跳 -5000／+5000 ms。`seek_relative()` 會限制在 0 到 duration 範圍內。Space 會切換播放／暫停。 |

> 不要在未實機測試 J/K/L 前重寫此區。尤其 J/K/L 同時採用 `QShortcut` 與 `keyPressEvent`，是目前行為的重要風險點。

## 7. 已知問題、限制與未完成項目

- **工作樹尚未封版：** 新增的 `controllers/`、`widgets/`、`core/project_state.py` 尚未 `git add`／commit；直接切換分支、清理或覆蓋可能遺失模組化成果。
- **`services/video_service.py` 有未提交修改：** 新增 OpenCV 取影格方法，但目前 main 不使用它們；不要假定倒播預覽已完成。
- **播放控制需實機回歸：** J/K/L 同時有快捷鍵與鍵盤事件處理；L 的 `forward_timer` 有實作但目前沒有 start 呼叫。尚未以真實影片完整驗證。
- **預覽路徑未接通：** `main.py` 有 `show_preview_frame()`，但目前沒有已確認的呼叫點；`VideoPanel` 的 preview 主要是預留 UI。
- **清除縮圖的資料一致性：** `clear_thumbnails()` 會刪除 JPG 並清空縮圖 UI，但不會移除 `shots` 或清空其 `thumbnail` 路徑；之後存檔／匯出可能保留失效縮圖資訊。
- **生成中取消或失敗：** 已生成的 Shot／JPG 不會 rollback；失敗時可能留下部分檔案或部分資料，且錯誤路徑不一定刷新 UI。
- **縮圖生成會清空既有 Shot：** `generate_thumbnails()` 在生成前執行 `self.shots.clear()`，包含手動建立的 Shot 與筆記。
- **無完整自動化測試套件：** 目前只有編譯與離屏 Qt 冒煙測試；沒有 pytest、真實影音檔回歸、FFmpeg 失敗情境或 UI 自動化測試。
- **版本快照限制：** `version/v1.2.0/` 不含根目錄目前所有 service/controller/widget，不能直接當作現行程式的完整替換來源。

## 8. 最近修改紀錄

### 已提交歷史（由新到舊）

- `ae27f0a`：服務層再分離，調整 `main.py` 與 `ProjectService`。
- `a4f1ec4`：Shot 與 Obsidian service 重構。
- `de9e353`：抽出 Shot model 與 Obsidian export service。
- `28bbf03`：抽出 `ShotService`。
- `607b0ab`：將 FFmpeg 處理移到 `VideoService`。
- `fce453a`／`636684e`：專案讀寫流程的早期模組化。

### 目前未提交的最近修改

- 將 `PlaybackController` 接入 main。
- 新增並接入 `ThumbnailTimeline`、`ShotPanel`、`VideoPanel`。
- 新增並接入 `ProjectState`、`ProjectController`。
- 在 `VideoService` 加入 OpenCV 影片／影格方法。

### 修改後曾出現或仍需留意的問題

- 近期首次以單行 Python 指令做 controller 測試時，因 `with` 無法放在該單行語法而產生 `SyntaxError`；測試命令已改寫後成功，這不是應用程式程式碼錯誤。
- `git diff --check` 目前仍回報 `main.py` EOF 的空白行；此檔案原本就有大量結尾空行，尚未在本次模組化中清理。
- 目前尚未以真實影片驗證新的 VideoPanel／PlaybackController 接線與 J/K/L 行為。

## 9. 穩定基準

**`v1.2.0` 是目前可辨識的穩定基準，不應直接覆蓋。**

依據：它是 Git 唯一 tag，且有 `version/v1.2.0/` 對應快照。根目錄目前已包含 tag 之後的已提交服務重構，以及未提交的模組化修改；若要大幅改寫、除錯或回退，先備份目前工作樹，再以 `v1.2.0` 作比較基線。

專案內未發現 `0.0.8` tag、資料夾或版本宣告；因此不能將 `0.0.8` 認定為目前穩定基準。

## 10. 測試狀態

最近成功執行：

```powershell
python -m py_compile .\main.py .\controllers\playback_controller.py .\controllers\project_controller.py .\core\project_state.py .\widgets\video_panel.py .\widgets\shot_panel.py .\widgets\thumbnail_timeline.py
```

- 結果：成功，沒有 Python 編譯錯誤。

最近成功執行的離屏 Qt 冒煙測試（設定 `QT_QPA_PLATFORM=offscreen`）：

- 建立 `ShotBreakdownAssistant` 主視窗成功。
- `QMediaPlayer` 正確指向 `VideoPanel.video_widget`。
- 影片時間軸、時間文字、播放按鈕狀態可更新。
- Shot 選取、景別顯示與筆記更新可同步至 `Shot` 資料。

最近成功執行的專案流程測試：

- 用暫存目錄儲存 `.shotproj.json`、重新載入後驗證影片路徑／間隔／筆記。
- 匯出 Obsidian Markdown，確認檔案生成。

尚未完成：實際開啟影音檔、產生縮圖、取消／失敗分支、J/K/L 回歸、Windows 封裝後測試。

## 11. 下一步（僅建議；由低風險到高風險）

1. **低：** 清理未使用 import、EOF 空白行，加入 type hints／docstrings；每次僅改小範圍並先跑編譯。
2. **低：** 為 `ProjectController`、`ShotService`、`ThumbnailService` 補非 UI 單元測試。
3. **中低：** 建立 `ThumbnailGenerationController`，僅把 `generate_thumbnails()` 的業務流程與取消／結果資訊抽出，Qt 進度視窗暫時留在 main。
4. **中：** 定義「清除縮圖」與「重新產生縮圖」對現有 Shot／筆記的產品規則，再改資料一致性流程。
5. **中高：** 在真實影片上驗證並統一 J/K/L 的單一事件路徑；確認後再移除未使用的 `forward_timer` 或真正接上它。不要在缺少實機回歸時直接重寫。
6. **高：** 完整將 main 的 property 轉接改為明確傳遞 `ProjectState`，並處理所有 UI 狀態／錯誤狀態。
7. **高：** 若要啟用 OpenCV 預覽倒播，需設計背景讀影格、生命週期釋放、UI 執行緒安全與大量影片效能測試。

## 12. AI 接手注意事項

- **不要隨意修改／覆蓋：** `version/v1.2.0/`、`ffmpeg/`、`ShotBreakdownAssistant.spec`、目前未提交的 `controllers/`、`widgets/`、`core/project_state.py`，以及已修改的 `services/video_service.py`。這些檔案分別是基準快照、執行相依、封裝設定與未封版工作。
- **目前已知可用：** 主視窗建立、Shot 清單／筆記／景別同步、專案 JSON 存取、Obsidian 匯出，以及模組匯入／離屏冒煙測試。
- **修改前先備份：** 至少備份整個專案工作樹，或建立 Git commit／stash；另備份 `main.py`、`services/video_service.py`、`controllers/`、`widgets/`、`core/project_state.py`。進行播放改動前，另備份一份可播放的測試影片與其 `.shotbreakdown_*` 縮圖目錄。
- **每次修改後最少執行：**

  ```powershell
  python -m py_compile .\main.py .\controllers\*.py .\core\*.py .\services\*.py .\widgets\*.py
  ```

  在 PowerShell 中 wildcard 可能與工具行為不同；若命令失敗，改為明確列出被改檔案。

- **涉及 UI／播放時還要執行：** 設定 `QT_QPA_PLATFORM=offscreen` 的主視窗冒煙測試，然後以真實影片人工驗證開檔、Space、J/K/L、左右跳轉、產生／清除縮圖、存檔／載入、Obsidian 匯出。
- **發布前：** 檢查 `git status --short`，將需要保留的新增模組納入 Git，處理或明確記錄 `services/video_service.py` 的未提交差異，並用 PyInstaller spec 在 Windows 測一次產物。
