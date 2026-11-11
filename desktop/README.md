# DM Ticket Assistant（桌面辅助版）

这是在原 Rust CLI 项目旁边新增的 Windows 桌面辅助程序。桌面版与旧版代码隔离，避免旧依赖和新依赖相互影响。

## 当前首个里程碑

- 使用 PySide6 提供 Windows 桌面界面。
- 保存演出名称、详情页 URL、Item ID、开售时间、购买数量和场次/票档优先级。
- 开售倒计时，到点后提醒用户。
- 在用户点击时打开大麦详情页，由用户自行登录并在官方页面完成验证、排队、选场次和订单提交。
- 用户确认订单已提交后，提醒其前往大麦 App 完成支付。
- 本地保存任务配置，不保存账号密码、Cookie、Token 或支付信息。

## 运行环境

- Windows 10/11
- Python 3.11 或更新版本

## 本地运行

在本目录打开 PowerShell：

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -e ".[dev]"
    python -m dm_ticket_assistant

## Windows EXE 打包

安装开发依赖后，在本目录运行：

    .\build_windows.ps1

生成文件位于 dist/DM-Ticket-Assistant/。

## 配置保存位置

Windows 默认保存到：

    %APPDATA%\DMTicketAssistant\task.json

配置仅包含任务信息。不要把 Cookie、访问令牌、密码或支付信息写入任务配置。

## 当前范围与安全边界

本程序是非官方的任务组织和提醒工具，不代表大麦官方产品，也不保证平台页面长期不变。

- 不读取、导出或保存大麦 Cookie、登录令牌或密码。
- 不调用大麦未公开的下单接口，不生成或伪造请求签名。
- 不绕过验证码、排队、风控、访问控制或其他平台验证。
- 不自动提交订单、不代替用户确认订单，也不处理支付。
- 登录、验证、排队、选座、订单提交及支付均由用户在官方页面或 App 中完成。

后续开发会优先完善任务管理、可访问页面信息的辅助展示、异常提示、日志、配置备份和打包测试。
