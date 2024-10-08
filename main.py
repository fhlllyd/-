import os
import sys
from datetime import datetime
import pandas as pd
from PySide6.QtCore import QTimer, QPoint
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                               QSpinBox, QDialog, QLineEdit, QMessageBox, QMainWindow, QWidget,
                               QStackedWidget, QTextEdit, QListWidget, QInputDialog)


class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 存储数据
        self.records = []
        self.paused = False
        self.current_interval = 0
        self.paused_time = None
        self.interval_minutes = 45
        self.rest_interval_minutes = 10
        self.remaining_time = 0
        self.is_resting = False  # 初始化为工作状态

        # 设置文件夹路径
        self.folder_path = "任务表"

        # 设置文件名
        self.filename = f"{datetime.now().strftime('%Y%m%d时间使用')}.csv"

        # 创建页面（初始化UI）
        self.initUI()

        # 检查当天文件是否存在并读取（必须在初始化UI后）
        self.check_existing_file()

    def check_existing_file(self):
        """检查是否有今天的文件存在，如果有则读取"""
        file_path = os.path.join(self.folder_path, self.filename)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:  # 检查文件是否存在且不为空
            try:
                df = pd.read_csv(file_path)
                existing_records = df.to_dict(orient='records')
                # 将文件中的记录加载到 self.records 中，避免重复保存
                self.records = existing_records
                for record in self.records:
                    self.update_task_display(record['时间段'], record['完成的事项'])
            except pd.errors.EmptyDataError:
                print("文件存在但为空，跳过读取。")
        else:
            print("没有找到文件或文件为空，跳过读取。")

    def initUI(self):
        self.setWindowTitle("Time Tracker")

        # 创建堆叆布局
        self.stacked_widget = QStackedWidget()

        # 创建第一个页面
        self.page1 = QWidget()
        self.init_page1()
        self.stacked_widget.addWidget(self.page1)

        # 创建第二个页面
        self.page2 = QWidget()
        self.init_page2()
        self.stacked_widget.addWidget(self.page2)

        self.setCentralWidget(self.stacked_widget)

        # Timer 初始化
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

    def init_page1(self):
        """页面1：设置时间间隔"""
        layout = QVBoxLayout()

        self.label1 = QLabel("设定工作时间间隔 (分钟):", self.page1)
        self.time_input = QSpinBox(self.page1)
        self.time_input.setRange(1, 120)  # 1-120 分钟
        self.time_input.setValue(45)

        self.label2 = QLabel("设定休息时间间隔 (分钟):", self.page1)
        self.rest_input = QSpinBox(self.page1)
        self.rest_input.setRange(1, 60)  # 1-60 分钟
        self.rest_input.setValue(10)

        self.confirm_button = QPushButton("确定", self.page1)
        self.confirm_button.clicked.connect(self.switch_to_page2)

        layout.addWidget(self.label1)
        layout.addWidget(self.time_input)
        layout.addWidget(self.label2)
        layout.addWidget(self.rest_input)
        layout.addWidget(self.confirm_button)

        self.page1.setLayout(layout)

    def init_page2(self):
        """页面2：显示倒计时和输入框"""
        layout = QVBoxLayout()

        # 倒计时显示
        self.timer_label = QLabel("剩余时间：00:00:00", self.page2)
        self.task_input = QLineEdit(self.page2)
        self.task_input.setPlaceholderText("请输入你在这个时间段内完成的事情")

        # 完成事项显示区（改成可选列表）
        self.task_display = QListWidget(self.page2)
        self.task_display.setSelectionMode(QListWidget.SingleSelection)  # 只允许选择一项

        # 按钮
        self.pause_button = QPushButton("暂停", self.page2)
        self.pause_button.clicked.connect(self.pause_tracking)

        self.end_button = QPushButton("结束", self.page2)
        self.end_button.clicked.connect(self.end_tracking)

        # 添加“切换任务”按钮
        self.switch_task_button = QPushButton("切换任务", self.page2)
        self.switch_task_button.clicked.connect(self.switch_task)

        # 添加“删除”和“修改”按钮
        self.delete_button = QPushButton("删除", self.page2)
        self.delete_button.clicked.connect(self.delete_task)

        self.edit_button = QPushButton("修改", self.page2)
        self.edit_button.clicked.connect(self.edit_task)
        # # 添加一个变量来跟踪上一次任务的结束时间
        # self.last_end_time = None

        # 布局
        layout.addWidget(self.timer_label)
        layout.addWidget(self.task_input)
        layout.addWidget(self.task_display)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.switch_task_button)  # 添加切换任务按钮
        button_layout.addWidget(self.edit_button)  # 添加修改按钮
        button_layout.addWidget(self.delete_button)  # 添加删除按钮
        button_layout.addWidget(self.end_button)

        layout.addLayout(button_layout)
        self.page2.setLayout(layout)

    def switch_to_page2(self):
        """切换到页面2并启动倒计时"""
        # 获取用户设置的时间间隔
        self.interval_minutes = self.time_input.value()
        self.rest_interval_minutes = self.rest_input.value()
        self.remaining_time = self.interval_minutes * 60  # 转换为秒

        # 将 last_end_time 初始化为当前时间，作为开始时间
        self.last_end_time = datetime.now().strftime("%H:%M:%S")

        self.update_timer_label()

        # 切换到页面2
        self.stacked_widget.setCurrentWidget(self.page2)

        # 开始倒计时
        self.timer.start(1000)

    def update_timer(self):
        """更新倒计时"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_timer_label()
        else:
            self.timer.stop()
            if self.is_resting:
                # 如果在休息状态，休息结束后弹出对话框让用户输入休息期间的事项
                self.show_rest_reminder()
            else:
                # 如果在工作状态，工作结束后显示提醒并切换到休息倒计时
                self.show_reminder()

    def update_timer_label(self):
        """更新倒计时显示"""
        minutes, seconds = divmod(self.remaining_time, 60)
        hours, minutes = divmod(minutes, 60)
        self.timer_label.setText(f"剩余时间：{hours:02}:{minutes:02}:{seconds:02}")

    def show_rest_reminder(self):
        """休息结束后显示提醒并要求输入休息期间的事项"""
        self.timer.stop()
        rest_reminder_dialog = ReminderDialog(self)
        if rest_reminder_dialog.exec():
            rest_activity = rest_reminder_dialog.get_input()

            # 使用 last_end_time 作为休息开始时间
            start_time = self.last_end_time

            # 当前时间为结束时间
            end_time = datetime.now().strftime("%H:%M:%S")
            time_period = f'{start_time} - {end_time}'

            # 更新 last_end_time 为当前的结束时间
            self.last_end_time = end_time

            # 检查记录是否已经存在，避免重复
            is_duplicate = any(
                record['时间段'] == time_period and record['完成的事项'] == rest_activity for record in self.records)

            if not is_duplicate:
                # 记录休息期间的事项
                self.records.append({
                    '时间段': time_period,
                    '完成的事项': rest_activity
                })

                # 更新完成事项显示区
                self.update_task_display(time_period, rest_activity)
                # 即时保存
                self.save_to_file()

        # 休息结束后，重新启动工作倒计时
        self.start_work_timer()

    def show_reminder(self):
        """显示提醒并要求输入"""
        self.timer.stop()
        reminder_dialog = ReminderDialog(self)
        if reminder_dialog.exec():
            activity = reminder_dialog.get_input()

            # 使用 last_end_time 作为开始时间
            start_time = self.last_end_time

            # 当前时间为结束时间
            end_time = datetime.now().strftime("%H:%M:%S")
            time_period = f'{start_time} - {end_time}'

            # 更新 last_end_time 为当前的结束时间
            self.last_end_time = end_time

            # 检查记录是否已经存在，避免重复
            is_duplicate = any(record['时间段'] == time_period and record['完成的事项'] == activity for record in self.records)

            if not is_duplicate:
                # 记录新的事项
                self.records.append({
                    '时间段': time_period,
                    '完成的事项': activity
                })

                # 更新完成事项显示区
                self.update_task_display(time_period, activity)
                # 即时保存
                self.save_to_file()

        # 启动休息倒计时
        self.start_rest_timer()

    def update_task_display(self, time_period, activity):
        """更新完成事项显示区"""
        # 添加新的完成任务到显示区
        self.task_display.addItem(f"{time_period} {activity}")

    def start_work_timer(self):
        """开始工作倒计时"""
        self.remaining_time = self.interval_minutes * 60
        self.update_timer_label()
        self.timer.start(1000)  # 启动工作倒计时

    def start_rest_timer(self):
        """开始休息倒计时"""
        self.is_resting = True  # 进入休息状态
        self.remaining_time = self.rest_interval_minutes * 60
        self.update_timer_label()
        self.timer.start(1000)

    def pause_tracking(self):
        """暂停功能，需要输入暂停原因"""
        if self.paused:
            # 继续，重新启动一个完整的倒计时
            pause_end_time = datetime.now()
            pause_duration = (pause_end_time - self.paused_time).total_seconds() / 60

            pause_reason_dialog = PauseReasonDialog(self)
            if pause_reason_dialog.exec():
                pause_reason = pause_reason_dialog.get_input()
                pause_time_period = f"{self.paused_time.strftime('%H:%M:%S')} - {pause_end_time.strftime('%H:%M:%S')}"

                # 记录暂停的时间段和原因
                self.records.append({
                    '时间段': pause_time_period,
                    '暂停原因': f"暂停原因: {pause_reason} (持续 {pause_duration:.2f} 分钟)"
                })

                self.update_task_display(pause_time_period, f"暂停原因: {pause_reason} (持续 {pause_duration:.2f} 分钟)")
                # 即时保存
                self.save_to_file()

            # 重置倒计时
            self.remaining_time = self.interval_minutes * 60
            self.update_timer_label()
            self.timer.start(1000)
            self.paused = False
            self.pause_button.setText("暂停")
        else:
            # 暂停前记录当前任务
            self.show_reminder()
            # 暂停
            self.timer.stop()
            self.paused = True
            self.paused_time = datetime.now()
            self.pause_button.setText("继续")

    def end_tracking(self):
        """结束当前工作周期"""
        # 先停止计时器
        self.timer.stop()

        # 提示用户输入完成的任务
        self.show_reminder()

        # 记录已经在 show_reminder 中保存过了，避免重复保存
        QMessageBox.information(self, "结束", "任务已保存，程序即将退出。")
        QApplication.quit()

    def switch_task(self):
        """切换任务"""
        if self.task_input.text():
            # 完成当前任务
            self.show_reminder()

    def delete_task(self):
        """删除选择的任务"""
        selected_row = self.task_display.currentRow()
        if selected_row >= 0:
            # 弹出确认对话框，确认是否删除
            reply = QMessageBox.question(self, '确认删除', '你确定要删除该任务吗？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # 从任务显示列表中删除选中的任务
                self.task_display.takeItem(selected_row)
                # 从记录中删除对应的任务
                del self.records[selected_row]
                # 保存到文件
                self.save_to_file()

    def edit_task(self):
        """修改选择的任务"""
        selected_row = self.task_display.currentRow()
        if selected_row >= 0:
            current_text = str(self.records[selected_row]['完成的事项'])  # 将 current_text 转换为字符串

            # 使用 QInputDialog 而不是 QMessageBox
            new_text, ok = QInputDialog.getText(self, "修改任务", "请输入新的任务描述:", QLineEdit.Normal, current_text)

            if ok and new_text:
                self.records[selected_row]['完成的事项'] = new_text
                self.task_display.item(selected_row).setText(f"{self.records[selected_row]['时间段']} {new_text}")
                self.save_to_file()

    def save_to_file(self):
        """保存记录到文件，防止重复保存"""
        # 如果文件夹不存在，则创建文件夹
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

        # 构建文件的完整路径
        file_path = os.path.join(self.folder_path, self.filename)

        # 将当前的 records 列表转换为 DataFrame
        df = pd.DataFrame(self.records)

        # 将 DataFrame 保存到 CSV 文件中，覆盖现有文件
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"保存记录到 {file_path}")


class ReminderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("任务提醒")

        # 设置窗口始终置顶
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout()
        self.label = QLabel("请输入你在这个时间段内完成的事项:", self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("请输入任务")

        self.button_box = QPushButton("确定", self)
        self.button_box.clicked.connect(self.accept)

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        # 初始化定时器，用于移动窗口
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_window)
        self.timer.start(100)  # 每100毫秒移动一次窗口

        self.move_direction = QPoint(50, 50)  # 初始化移动方向（每次移动的像素值）

    def get_input(self):
        return self.text_edit.toPlainText()

    def move_window(self):
        """让窗口在屏幕内来回移动"""
        current_pos = self.pos()
        new_x = current_pos.x() + self.move_direction.x()
        new_y = current_pos.y() + self.move_direction.y()

        # 获取屏幕的尺寸
        screen_rect = QApplication.primaryScreen().availableGeometry()

        # 检查窗口是否碰到屏幕边缘，碰到时改变方向
        if new_x <= 0 or new_x + self.width() >= screen_rect.width():
            self.move_direction.setX(-self.move_direction.x())
        if new_y <= 0 or new_y + self.height() >= screen_rect.height():
            self.move_direction.setY(-self.move_direction.y())

        # 移动窗口到新的位置
        self.move(new_x, new_y)

    def enterEvent(self, event):
        """当鼠标进入窗口时停止移动"""
        self.timer.stop()  # 停止移动
        super().enterEvent(event)

    def leaveEvent(self, event):
        """当鼠标离开窗口时继续移动"""
        self.timer.start(100)  # 重新开始移动
        super().leaveEvent(event)


class PauseReasonDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("暂停原因")

        layout = QVBoxLayout()
        self.label = QLabel("请输入暂停的原因:", self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("请输入原因")

        self.button_box = QPushButton("确定", self)
        self.button_box.clicked.connect(self.accept)

        layout.addWidget(self.label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_input(self):
        return self.text_edit.toPlainText()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec())
