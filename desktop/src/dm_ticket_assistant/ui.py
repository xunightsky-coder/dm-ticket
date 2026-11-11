from __future__ import annotations

import webbrowser
from datetime import datetime

from PySide6.QtCore import QDateTime, QTimer
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .config_store import default_config_path, load_task, save_task
from .models import PriorityOption, TicketTask, is_damai_url
from .scheduler import format_countdown, seconds_until


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DM Ticket Assistant")
        self.resize(900, 720)

        self._target: datetime | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self.update_countdown)

        self.event_name = QLineEdit()
        self.event_name.setPlaceholderText("例如：某某演唱会")
        self.event_url = QLineEdit()
        self.event_url.setPlaceholderText("https://m.damai.cn/...")
        self.item_id = QLineEdit()
        self.item_id.setPlaceholderText("详情页 URL 中的 itemId（可选）")

        self.sale_time = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.sale_time.setCalendarPopup(True)
        self.sale_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self.quantity = QSpinBox()
        self.quantity.setRange(1, 20)
        self.quantity.setValue(1)

        self.priority_table = QTableWidget(0, 3)
        self.priority_table.setHorizontalHeaderLabels(["场次（优先级顺序）", "票档", "价格备注"])
        self.priority_table.horizontalHeader().setStretchLastSection(True)
        self.priority_table.setMinimumHeight(150)

        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText("可填写实名观演人准备情况、出行备注等；请勿填写密码或 Cookie。")
        self.notes.setMaximumHeight(90)

        self.countdown_label = QLabel("尚未启动倒计时")
        self.countdown_label.setStyleSheet("font-size: 22px; font-weight: 600;")
        self.status_label = QLabel("准备就绪")
        self.status_label.setWordWrap(True)

        self._build_ui()
        self._load_saved_task()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        intro = QLabel(
            "用于整理购票任务、开售提醒和人工支付交接。登录、验证、排队、"
            "选场次及提交订单均由你在大麦官方页面完成。"
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        task_group = QGroupBox("演出任务")
        form = QFormLayout(task_group)
        form.addRow("演出名称", self.event_name)
        form.addRow("大麦详情页 URL", self.event_url)
        form.addRow("Item ID", self.item_id)
        form.addRow("开售时间", self.sale_time)
        form.addRow("购买数量", self.quantity)
        root.addWidget(task_group)

        priority_group = QGroupBox("场次 / 票档优先级（从上到下）")
        priority_layout = QVBoxLayout(priority_group)
        priority_layout.addWidget(self.priority_table)
        priority_buttons = QHBoxLayout()
        add_priority = QPushButton("添加优先级")
        remove_priority = QPushButton("删除选中行")
        add_priority.clicked.connect(self.add_priority)
        remove_priority.clicked.connect(self.remove_priority)
        priority_buttons.addWidget(add_priority)
        priority_buttons.addWidget(remove_priority)
        priority_buttons.addStretch(1)
        priority_layout.addLayout(priority_buttons)
        root.addWidget(priority_group)

        notes_group = QGroupBox("备注")
        notes_layout = QVBoxLayout(notes_group)
        notes_layout.addWidget(self.notes)
        root.addWidget(notes_group)

        countdown_group = QGroupBox("开售提醒")
        countdown_layout = QVBoxLayout(countdown_group)
        countdown_layout.addWidget(self.countdown_label)
        countdown_layout.addWidget(self.status_label)
        countdown_actions = QHBoxLayout()
        self.start_button = QPushButton("启动倒计时")
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_countdown)
        self.stop_button.clicked.connect(self.stop_countdown)
        countdown_actions.addWidget(self.start_button)
        countdown_actions.addWidget(self.stop_button)
        countdown_actions.addStretch(1)
        countdown_layout.addLayout(countdown_actions)
        root.addWidget(countdown_group)

        actions = QHBoxLayout()
        save_button = QPushButton("保存任务")
        open_button = QPushButton("打开大麦详情页")
        submitted_button = QPushButton("我已提交订单")
        save_button.clicked.connect(self.save_current_task)
        open_button.clicked.connect(self.open_event_page)
        submitted_button.clicked.connect(self.confirm_order_submitted)
        actions.addWidget(save_button)
        actions.addWidget(open_button)
        actions.addStretch(1)
        actions.addWidget(submitted_button)
        root.addLayout(actions)

        footer = QLabel(
            "安全提示：本程序不保存 Cookie / Token，不调用未公开下单接口，"
            "不绕过验证码、排队或风控，也不会自动提交订单或支付。"
        )
        footer.setWordWrap(True)
        footer.setStyleSheet("color: #777;")
        root.addWidget(footer)

        self.setCentralWidget(central)
        self.add_priority()

    def _load_saved_task(self) -> None:
        try:
            task = load_task()
        except (OSError, ValueError, TypeError) as exc:
            self.status_label.setText(f"读取本地配置失败：{exc}")
            return

        if task is None:
            return

        self.event_name.setText(task.event_name)
        self.event_url.setText(task.event_url)
        self.item_id.setText(task.item_id)
        self.quantity.setValue(task.quantity)
        self.notes.setPlainText(task.notes)

        if task.sale_time:
            try:
                timestamp = datetime.fromisoformat(task.sale_time).timestamp()
                self.sale_time.setDateTime(QDateTime.fromSecsSinceEpoch(int(timestamp)))
            except ValueError:
                pass

        self.priority_table.setRowCount(0)
        for option in task.priorities:
            self.add_priority(option)

        if not task.priorities:
            self.add_priority()

        self.status_label.setText(f"已载入本地任务：{default_config_path()}")

    def add_priority(self, option: PriorityOption | None = None) -> None:
        row = self.priority_table.rowCount()
        self.priority_table.insertRow(row)
        values = (
            option.session if option else "",
            option.ticket_tier if option else "",
            option.price if option else "",
        )
        for column, value in enumerate(values):
            self.priority_table.setItem(row, column, QTableWidgetItem(value))

    def remove_priority(self) -> None:
        row = self.priority_table.currentRow()
        if row >= 0:
            self.priority_table.removeRow(row)

    def _task_from_form(self) -> TicketTask:
        sale_timestamp = self.sale_time.dateTime().toSecsSinceEpoch()
        sale_time = datetime.fromtimestamp(sale_timestamp).isoformat(timespec="seconds")

        priorities: list[PriorityOption] = []
        for row in range(self.priority_table.rowCount()):
            values = []
            for column in range(3):
                item = self.priority_table.item(row, column)
                values.append(item.text().strip() if item else "")
            if any(values):
                priorities.append(
                    PriorityOption(
                        session=values[0],
                        ticket_tier=values[1],
                        price=values[2],
                    )
                )

        return TicketTask(
            event_name=self.event_name.text().strip(),
            event_url=self.event_url.text().strip(),
            item_id=self.item_id.text().strip(),
            sale_time=sale_time,
            quantity=self.quantity.value(),
            priorities=priorities,
            notes=self.notes.toPlainText().strip(),
        )

    def save_current_task(self) -> None:
        try:
            task = self._task_from_form()
            path = save_task(task)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "无法保存", str(exc))
            return

        self.status_label.setText(f"任务已保存：{path}")
        QMessageBox.information(self, "保存成功", "任务配置已保存在本地。")

    def open_event_page(self) -> None:
        url = self.event_url.text().strip()
        item_id = self.item_id.text().strip()

        if item_id and not item_id.isdigit():
            QMessageBox.warning(self, "Item ID 无效", "Item ID 只能包含数字。")
            return

        if not url and item_id:
            url = f"https://m.damai.cn/damai/detail/item.html?itemId={item_id}"

        if not is_damai_url(url):
            QMessageBox.warning(
                self,
                "链接无效",
                "请填写 HTTPS 的大麦官方详情页 URL，或填写有效的数字 Item ID。",
            )
            return

        opened = webbrowser.open(url)
        if opened:
            self.status_label.setText("已请求打开大麦详情页，请在浏览器中自行登录并操作。")
        else:
            self.status_label.setText("浏览器未能自动打开，请复制详情页 URL 手动访问。")

    def start_countdown(self) -> None:
        try:
            task = self._task_from_form()
            task.validate()
        except ValueError as exc:
            QMessageBox.warning(self, "任务信息不完整", str(exc))
            return

        self._target = datetime.fromtimestamp(
            self.sale_time.dateTime().toSecsSinceEpoch()
        )
        self._timer.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("倒计时运行中；到点后提醒你切换到官方页面。")
        self.update_countdown()

    def stop_countdown(self) -> None:
        self._timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.countdown_label.setText("倒计时已停止")
        self.status_label.setText("已停止倒计时。")

    def update_countdown(self) -> None:
        if self._target is None:
            return

        remaining = seconds_until(self._target)
        if remaining <= 0:
            self._timer.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.countdown_label.setText("开售时间已到")
            self.status_label.setText("请在大麦官方页面自行完成后续操作。")
            QMessageBox.information(
                self,
                "开售提醒",
                "已到达设定的开售时间。请前往大麦官方页面自行操作。",
            )
            return

        self.countdown_label.setText(f"距离开售：{format_countdown(remaining)}")

    def confirm_order_submitted(self) -> None:
        answer = QMessageBox.question(
            self,
            "确认订单状态",
            "请确认你已经在大麦官方页面看到订单提交成功。\n\n"
            "确认后，本程序会提醒你前往大麦 App 完成支付；本程序不会代替你支付。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self,
                "请完成支付",
                "请立即打开大麦 App，在订单页面核对订单信息并完成支付。",
            )
            self.status_label.setText("用户已确认订单提交成功，等待在大麦 App 完成支付。")
