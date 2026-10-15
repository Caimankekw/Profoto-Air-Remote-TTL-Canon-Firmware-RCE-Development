# AIR2-P8-FIX1 Windows 更新包

[English](README.md) · 开发者：**Caimankekw** · **2026-10-16** · 标签 `p8-fix1-20261016`

这是适用于 **Air Remote TTL-C（Canon）** 的实验自定义固件，不是 Profoto 官方发布。原创自定义代码采用 AGPL-3.0-only，厂商固件及更新器保留原有条款。使用前请阅读[免责声明](DISCLAIMER.zh-CN.md)、[LICENSE](LICENSE) 和 [NOTICE](NOTICE.zh-CN.md)。

**FIX1 尚未经过真机开机或相机测试。**它修复 AIR1 相对数值到期时因原生事务忙而残留的问题：忙时保留已到期的期限，恢复就绪后清理相对数值。radio、persistence 和 HSS-P3 沿用 P8。历史 P8 真机结果不代表本镜像已通过验证。详情见[变更记录](CHANGELOG.zh-CN.md)。

源码：[FIX1 固件与工具](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/p8-fix1-20261016) · [Windows 封装代码](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/p8-fix1-20261016/windows)。[main 分支](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main) 单独保存原始 C11 逆向材料。

随包 `source.zip` 是本次安装包精确对应的源码快照，SHA256 记录在 `package_manifest.json`，其中的 `source_manifest.json` 标识每项源码文件。复现本包时请使用这份随包快照；对应发布标签为 `p8-fix1-20261016`。

## 使用方法

1. 运行安装包，选择简体中文或英文，阅读免责声明和许可，选择尚不存在的新目录。默认解压至 `%LOCALAPPDATA%\Caimankekw\AirRemote-TTL-C\AIR2-P8-FIX1`。外壳不安装驱动，也不刷写设备。
2. 完成页的“打开更新器”可选，**默认不勾选**。也可在解压目录手动打开 `AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe`。使用便携 ZIP 时先完整解压。
3. 连接目标 Air Remote TTL-C，遵循原厂图形界面提示。确认识别的设备后，手动点击其更新按钮，保持连接直到完成。
4. 断开 USB，用电池正常开机，先检查启动、按键和显示，再进行相机测试。若出现 `EC!` 且原厂 GUI 仍能通信，可使用 `restore_original/Air-Remote-TTL-C-Firmware-C11.exe` 尝试恢复 C11；不保证可恢复。

固件资源以外的原 GUI 和 loader 字节保持不变，不提供替代命令行刷写器。外层解压向导使用普通用户权限；原更新器自身的运行条件不因此改变。修改后的更新器原厂签名已失效，外壳未签名；本包不宣称厂商认证。

## FIX1 操作

- **C＋HEAD**：TTL 与 MAN 均可切换 ABC/DEF 页。
- **C＋MODEL**：MAN 下切换 AIR1/AIR2；TTL 下吞掉组合且不改上次手动类型。两种组合不应额外开关 Head/Model。
- **A、B、加、减**：不增加组合等待。原扫描、长短按判定及未完成无线事务仍会影响响应；忙时本轮调节可能不被接受，不会排队补发，需要松开后重按。
- AIR1 仅在成功调节后临显数值；若到期时遇忙，FIX1 保留已到期的期限，恢复就绪后隐藏。已启用 AIR2 目标持续显示。TTL 的 ABC 仍为曝光补偿，DEF 使用记住的 AIR1/AIR2 手动控制，**不是六组自动 TTL**。

决定测试本候选后，请检查 MAN 和 TTL DEF 的 AIR1 到期隐藏及忙转闲恢复，并检查 AIR2 持续显示。在未到上下界时检查连续短按加号五次增加 0.5、减号五次减少 0.5，分别核对屏幕和实际灯具。两种组合键、DEF 接收设置与实际引闪要分别检查。完整行为和边界见 `source.zip` 内根 README 及 `C11/`。

## 内容与校验

- 冻结的 AIR2-P8-FIX1 GUI、原厂 C11 恢复 GUI、对应源码 `source.zip`。
- 中英文说明、免责声明、NOTICE 和变更记录，LICENSE 及 NSIS 许可。
- `package_manifest.json` 与 `SHA256SUMS.txt` 标识解压后的文件字节。

AIR2-P8-FIX1 更新器 SHA256：`f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed`。

预期固件镜像 SHA256：`a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8`。partial BIN 是构建与研究产物，禁止直接刷写。

外壳不修改此更新器及固件。构建检查输入哈希、源码 ZIP、PE 资源、便携 ZIP，以及静态解包后的 NSIS 内容；不执行更新器或安装器，不访问 USB。离线通过不代表真机启动、射频接收或实拍表现通过；实际完成的检查以包构建报告为准。

重建外壳请解压 `source.zip` 并参照 `windows/README.zh-CN.md`。使用交付的更新器不需要 Python。对应源码随包提供；原工具及来自厂商固件的输入保留各自权利。外壳使用未修改的 NSIS 3.13 组件，许可见 `NSIS-COPYING.txt`，源码见 [NSIS 项目](https://sourceforge.net/projects/nsis/files/NSIS%203/3.13/)。
