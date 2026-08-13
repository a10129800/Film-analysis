from pathlib import Path

p = Path("main_v12_clean.py")
s = p.read_text(encoding="utf-8")

old = """        self.shot_label = QLabel(
            "尚未選擇 SHOT"
        )

        shot_layout.addWidget(
            self.shot_label
        )

        self.note_editor = QTextEdit()
"""

new = """        self.shot_label = QLabel(
            "尚未選擇 SHOT"
        )

        shot_layout.addWidget(
            self.shot_label
        )

        # =====================================================
        # v1.2：景別
        # =====================================================

        shot_layout.addWidget(
            QLabel(" 景別")
        )

        self.shot_size_buttons = []

        shot_size_layout = QHBoxLayout()

        for text in [
            "大特寫",
            "特寫",
            "中景",
            "全景",
            "大全景"
        ]:

            button = QPushButton(
                text
            )

            button.setCheckable(
                True
            )

            self.shot_size_buttons.append(
                button
            )

            shot_size_layout.addWidget(
                button
            )

        shot_layout.addLayout(
            shot_size_layout
        )

        self.note_editor = QTextEdit()
"""

if old not in s:
    raise SystemExit("找不到插入位置，沒有修改檔案")

p.write_text(
    s.replace(old, new, 1),
    encoding="utf-8"
)

print("完成：景別按鈕 UI 已加入")
