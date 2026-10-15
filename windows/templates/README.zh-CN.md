# AIR2-P8 Windows 更新包

[English](README.md) · 开发者：**Caimankekw**

这是适用于 **Air Remote TTL-C（Canon）** 的实验自定义固件，不是 Profoto 官方发布。原创自定义代码采用 AGPL-3.0-only，厂商固件及更新器保留原有条款。使用前请阅读[免责声明](DISCLAIMER.zh-CN.md)、[LICENSE](LICENSE) 和 [NOTICE](NOTICE.md)。

源码：[P8 固件与工具](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8) · [Windows 封装代码](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8/windows)。[main 分支](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main) 单独保存原始 C11 逆向材料。

随包 `source.zip` 是本次安装包精确对应的源码快照，SHA256 记录在 `package_manifest.json`，其中的 `source_manifest.json` 标识每项源码文件。线上 P8 分支可能继续更新，复现本包时请使用这份随包快照。

## 使用方法

1. 运行安装包，选择简体中文或英文，阅读免责声明和许可，选择尚不存在的新目录。默认解压至 `%LOCALAPPDATA%\Caimankekw\AirRemote-TTL-C\AIR2-P8`。外壳不安装驱动，也不刷写设备。
2. 完成页的“打开更新器”可选，**默认不勾选**。也可在解压目录手动打开 `AirRemote_TTL_C_C11_AIR2_P8_Caimankekw_EXPERIMENTAL.exe`。使用便携 ZIP 时先完整解压。
3. 连接目标 Air Remote TTL-C，遵循原厂图形界面提示。确认识别的设备后，手动点击其更新按钮，保持连接直到完成。
4. 断开 USB，用电池正常开机，先检查启动、按键和显示，再进行相机测试。若出现 `EC!`，使用 `restore_original/Air-Remote-TTL-C-Firmware-C11.exe` 的原厂图形界面恢复 C11。

固件资源以外的原 GUI 和 loader 字节保持不变，不提供替代命令行刷写器。外层解压向导使用普通用户权限；原更新器自身的运行条件不因此改变。本包不宣称官方签名或厂商认证。

## P8 操作

- **C＋HEAD**：TTL 与 MAN 均可切换 ABC/DEF 页。
- **C＋MODEL**：MAN 下切换 AIR1/AIR2；TTL 下吞掉组合且不改上次手动类型。两种组合不应额外开关 Head/Model。
- **A、B、加、减**：不增加组合等待。原扫描、长短按判定及未完成无线事务仍会影响响应；忙时本轮调节可能不被接受，不会排队补发，需要松开后重按。
- AIR1 仅在成功调节后临显数值，空闲后隐藏；已启用 AIR2 目标持续显示。TTL 的 ABC 仍为曝光补偿，DEF 使用记住的 AIR1/AIR2 手动控制，**不是六组自动 TTL**。

请在未到上下界时检查连续短按加号五次增加 0.5、减号五次减少 0.5，分别核对屏幕和实际灯具。DEF 接收设置与实际引闪要分开检查。完整行为和边界见 `source.zip` 内根 README 及 `C11/`。

## 内容与校验

- 冻结的 AIR2-P8 GUI、原厂 C11 恢复 GUI、对应源码 `source.zip`。
- 中英文说明和免责声明、LICENSE、NOTICE 及 NSIS 许可。
- `package_manifest.json` 与 `SHA256SUMS.txt` 标识解压后的文件字节。

AIR2-P8 更新器 SHA256：`dec0660b9568713d36a13e44909741b2891d30680895f0ef3406a31e9cbebde1`。

外壳不修改此更新器及固件。构建检查输入哈希、源码 ZIP、PE 资源、便携 ZIP，以及静态解包后的 NSIS 内容；不执行更新器或安装器，不访问 USB。离线通过不代表真机启动、射频接收或实拍表现通过；实际完成的检查以包构建报告为准。

重建外壳请解压 `source.zip` 并参照 `windows/README.zh-CN.md`。使用交付的更新器不需要 Python。对应源码随包提供；原工具及来自厂商固件的输入保留各自权利。外壳使用未修改的 NSIS 3.13 组件，许可见 `NSIS-COPYING.txt`，源码见 [NSIS 项目](https://sourceforge.net/projects/nsis/files/NSIS%203/3.13/)。
