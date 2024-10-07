import sys
import time
import os
import pandas as pd
from datetime import datetime
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                               QSpinBox, QDialog, QLineEdit, QMessageBox, QMainWindow, QWidget,
                               QStackedWidget, QTextEdit, QListWidget)


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

        # 设置文件夹路径
        self.folder_path = "任务表"

        # 设置文件名
        self.filename = f"{datetime.now().strftime('%Y%m%d时间使用')}.csv"

        # 检查当天文件是否存在并读取
        self.check_existing_file()

        # 创建页面
        self.initUI()

    def check_existing_file(self):
        """检查是否有今天的文件存在，如果有则读取"""
        file_path = os.path.join(self.folder_path, self.filename)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:  # 检查文件是否存在且不为空
            try:
                df = pd.read_csv(file_path)
                # 把已保存的记录加载到 self.records 中
                self.records = df.to_dict(orient='records')
                # 更新任务显示区
                for record in self.records:
                    self.update_task_display(record['时间段'], record['完成的事项'])
            except pd.errors.EmptyDataError:
                print("文件存在但为空，跳过读取。")
        else:
            print("没有找到文件或文件为空，跳过读取。")

    def initUI(self):
        self.setWindowTitle("Time Tracker")

        # 创建堆叠布局
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
            self.show_reminder()

    def update_timer_label(self):
        """更新倒计时显示"""
        minutes, seconds = divmod(self.remaining_time, 60)
        hours, minutes = divmod(minutes, 60)
        self.timer_label.setText(f"剩余时间：{hours:02}:{minutes:02}:{seconds:02}")

    def show_reminder(self):
        """显示提醒并要求输入"""
        self.timer.stop()
        reminder_dialog = ReminderDialog(self)
        if reminder_dialog.exec():
            activity = reminder_dialog.get_input()
            start_time = (datetime.now() - pd.Timedelta(minutes=self.interval_minutes)).strftime("%H:%M:%S")
            end_time = datetime.now().strftime("%H:%M:%S")
            time_period = f'{start_time} - {end_time}'

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

    def start_rest_timer(self):
        """开始休息倒计时"""
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

    def switch_task(self):
        """切换任务"""
        self.timer.stop()
        self.show_reminder()  # 结束当前任务
        self.remaining_time = self.interval_minutes * 60  # 重置倒计时
        self.update_timer_label()
        self.timer.start(1000)  # 开始新的任务倒计时

    def end_tracking(self):
        """结束并保存数据"""
        self.timer.stop()
        self.save_to_file()
        self.close()

    def delete_task(self):
        """删除选中的任务记录"""
        selected_item = self.task_display.currentRow()
        if selected_item >= 0:
            # 删除记录
            del self.records[selected_item]
            self.task_display.takeItem(selected_item)
            self.save_to_file()

    def edit_task(self):
        """修改选中的任务记录"""
        selected_item = self.task_display.currentRow()
        if selected_item >= 0:
            # 打开修改对话框
            edit_dialog = ReminderDialog(self)
            if edit_dialog.exec():
                updated_activity = edit_dialog.get_input()

                # 更新 records 和显示区
                self.records[selected_item]['完成的事项'] = updated_activity
                time_period = self.records[selected_item]['时间段']
                self.task_display.item(selected_item).setText(f"{time_period} {updated_activity}")

                # 保存修改
                self.save_to_file()

    def save_to_file(self):
        """保存数据到 CSV 文件"""

        # 检查文件夹是否存在，如果不存在则创建
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

        # 生成完整的文件路径
        file_path = os.path.join(self.folder_path, self.filename)

        # 将记录保存到 CSV 文件
        df = pd.DataFrame(self.records)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')


class ReminderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("提醒")
        self.setWindowFlag(Qt.WindowStaysOnTopHint)  # 窗口置顶

        self.label = QLabel("请输入你在这个时间段内完成了什么:", self)
        self.input_field = QLineEdit(self)

        self.ok_button = QPushButton("确定", self)
        self.ok_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.input_field)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_input(self):
        return self.input_field.text()


class PauseReasonDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("暂停原因")
        self.setWindowFlag(Qt.WindowStaysOnTopHint)  # 窗口置顶

        self.label = QLabel("请输入暂停原因:", self)
        self.input_field = QLineEdit(self)

        self.ok_button = QPushButton("确定", self)
        self.ok_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.input_field)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_input(self):
        return self.input_field.text()


def main():
    app = QApplication(sys.argv)
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
