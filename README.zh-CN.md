# Air Remote TTL-C · AIR2-P8-FIX1

[English](README.md) | 简体中文

开发者：[Caimankekw](https://github.com/Caimankekw) · 原创代码：[AGPL-3.0-only](LICENSE)

用于 **Profoto Air Remote TTL-C（Canon），C11** 的非官方实验固件。本项目通过逆向分析和二进制补丁，从源码构建 AIR2-P8-FIX1 并封装进原 C11 图形更新器。它不是厂商完整 C 源码，不适用于 Connect、Connect Pro 或其他相机卡口版本。

**FIX1 尚未进行实机启动或相机测试。** 它是基于 AIR2-P8 的独立修复候选，原 P8 文件与发布包保留为历史版本。现有 P8 用户需要下载新的 FIX1 更新器，先阅读[免责声明](DISCLAIMER.zh-CN.md)，再在其图形界面中手动刷写。下载或解压安装包不会更新设备。

这是 [Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development) 的 **P8 开发分支**。[main 分支](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main) 提供未修改 C11 固件的分析资料和离线分析工具。本次标签为 `p8-fix1-20261016`；安装包、对应源码提交和哈希见 [Releases](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases)，[旧 P8 发布](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases/tag/p8-20261015)及版本历史见[更新记录](CHANGELOG.zh-CN.md)。

## FIX1 修复内容

AIR1 相对功率数字到期时，如果无线发送、相机模式请求或旧发送事务正忙，P8 会先清除原生显示期限，再因忙而放弃隐藏数字；后续清理失去了可重试的期限，数字可能一直显示。FIX1 在忙时保留已经到期的期限，恢复就绪后完成六组相对值清零和隐藏。准备状态只检查一次，消费期限与清理相对值走同一成功路径。

本次没有增加 RAM 或调整定时周期。AIR2 常驻数字、TTL ABC 曝光补偿、目标功率、开关和页面／模式记忆保持原实现。无线、持久化组件及 HSS-P3 保护区与 P8 逐字节相同。

## 功能与操作

- MAN-AIR1：相对功率调节，调节后临时显示数字。
- MAN-AIR2：绝对目标功率，当前页已开启组的数字常驻显示。
- **C＋HEAD**：切换 ABC / DEF 页，适用于 TTL 和两种手动模式。
- **C＋MODEL**：在 MAN 中切换 AIR1 / AIR2；TTL 中忽略此组合，不改变记住的手动类型。
- A、B、加减键保留正常短按／长按路径，不等待组合键窗口。
- MODE 切换 TTL / MAN，进入 MAN 时恢复上次手动类型。
- ALL 作用于六组；记住六组 AIR2 目标、闪光与造型灯开关、页面和模式。
- 保留既有 HSS-P3 运行路径。

**TTL 的 ABC 是曝光补偿，DEF 按记住的手动类型工作，并非六组自动 TTL。** 固定液晶 ABC 字母不能变成 DEF；DEF 页隐藏这些行标，切页时短暂显示 d/E/F。

只有 C、HEAD、MODEL 等待组合确认，因此其单键动作可能有延迟；组合生效后请完全松开两键。原加减双键和 A＋减号快捷键已移除，按原生单键优先级处理。同步发送、保存和扫描仍限制输入速度；忙时用户操作可能被拒绝，不会排队补发。

AIR2 目标范围为 0.1–10.0，但具体灯具的最低输出可能更高。显示值是引闪器请求，不是灯端实时回读。首次安装或旧记录迁移时，DEF 默认关闭、目标为 5.0。重新安装可能重置新增设置。

## 目录

| 路径 | 内容 |
| --- | --- |
| [C11](C11/README.zh-CN.md) | 精简原厂固件分析及恢复逻辑 |
| [source](source/README.zh-CN.md) | UI、六组无线、持久化、HSS 补丁与链接器 |
| `tools/` | 容器、编码、反汇编、复现及源码打包工具 |
| [reference](reference/README.zh-CN.md) | 通用地址变换参数与指纹，不含设备备份 |
| [windows](windows/README.zh-CN.md) | Windows 自解压包构建源码 |
| [tests](tests/README.zh-CN.md) | 独立构建检查及分开标识的 FIX1／P8 验证记录 |
| [inputs](inputs/README.md) | 用户自备原厂输入要求；源码包不含原厂 EXE |

## 从源码构建

需要 Python **3.9 或更新版本**。固件构建只使用标准库，不需要旧开发工作区或中间版本。提供未修改的 `Air-Remote-TTL-C-Firmware-C11.exe`，在项目根目录运行：

```powershell
python -B build.py --original "inputs\Air-Remote-TTL-C-Firmware-C11.exe"
python -I -B tests/test_build.py --original "inputs\Air-Remote-TTL-C-Firmware-C11.exe" -v
python -I -B tests/test_isolated_build.py --original "inputs\Air-Remote-TTL-C-Firmware-C11.exe"
python -B tools/package_source.py
```

原厂 EXE 的 SHA-256 必须为 `e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240`。

构建解码该输入，执行 HSS／AIR2 源码生成器，链接并检查 CRC／编码，输出到 `build/`。构建不会运行更新器或访问 USB。源码包不包含原厂 EXE；Windows 包内未修改的原厂恢复 EXE 可作为该输入。

| 冻结固件产物 | SHA-256 |
| --- | --- |
| `AIR2-P8-FIX1.base4000.partial.bin` | `a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8` |
| `AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe` | `f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed` |

分析 BIN 的前两个明文字节仍未知：**不能直接刷写 partial BIN**。安装应使用 EXE 图形更新器。重建保留原厂 GUI、loader、未知首字、稀疏布局和尾部；修改固件资源后，原厂签名不再有效。

## Windows 安装包

本次发布提供：

- `Profoto-AirRemote-TTL-C-AIR2-P8-FIX1-Custom-Updater.exe`：NSIS 自解压封装。
- `AirRemote-TTL-C-AIR2-P8-FIX1-Windows-portable.zip`：Windows 便携包。
- `Profoto-AirRemote-TTL-C-AIR2-P8-FIX1-Source.zip`：对应的整合源码包。

Windows 包含自定义图形更新器、未修改的原厂恢复 GUI、对应源码、双语说明、许可和免责声明。NSIS 外壳解压到用户目录，完成页可选择打开 GUI。**刷写固件仍需用户在更新器中手动操作。** 使用安装包不需要 Python；构建外壳需要 NSIS 与 7-Zip，见 [Windows 构建说明](windows/README.zh-CN.md)。

本次源码包包含整合后的仓库文档，完整的 `C11/`、`windows/`、`inputs/` 源码／说明目录，以及 `.gitignore`、`.gitattributes`，仍不包含原厂 EXE。它区别于此前 SHA-256 为 `14649a975625fc3ed72b5ac0a9237ad5b622e76905fa0b831404c34962728141` 的冻结 FIX1 输入源码包。该哈希仅标识输入档案，不能用于核对本次源码附件；新附件以发布校验和为准，上述固件哈希保持固定。

## 验证范围

冻结 FIX1 报告记录了 77 项真实原生期限路径回放，包含 24 项冻结 P8 失败对照、忙转空闲、单次就绪检查后再次变忙、计时回绕和 AIR2 负例。报告还记录 UI 470 项、无线 1,944 项、持久化 717 项、整合 333 项回归，以及 13 项源码构建、13 项容器、7 项参考编码检查和隔离重建。[tests/VERIFICATION.json](tests/VERIFICATION.json) 将该报告与旧 P8 验证分开保存。

PIC18 回放中的时钟、UART、Flash 和 LCD 为有边界的模型。这些检查不能证明设备启动、物理按键速率、射频接收、曝光、掉电行为或新的 HSS 实机测量结果。完整行为回放依赖原开发工作区；精简源码包提供独立构建和容器测试。

手动更新后，请检查 MAN 与 TTL DEF 中 AIR1 数字到期隐藏、AIR2 数字常驻、五次加号增加 0.5 且五次减号恢复、两个组合键不误改闪光／造型灯开关，以及重启后模式和设置保留。显示是否正确与灯具实际行为需分别检查。原厂恢复 GUI 不保证故障后可恢复。

使用前阅读[免责声明](DISCLAIMER.zh-CN.md)、[许可范围](NOTICE.zh-CN.md)和 [LICENSE](LICENSE)。AGPL-3.0-only 仅适用于开发者的原创范围，不将原厂固件、更新器或混合二进制整体重新许可。

## macOS 更新包

原生 Mac 封包说明与源码见 [macos/README.zh-CN.md](macos/README.zh-CN.md)。Mac 包保留原厂 GUI 与 USB 加载器，置入与现有 Windows 版完全相同的固件 HEX，以 ad-hoc 签名重建外层应用资源密封，再生成 APFS/UDZO DMG。它不具备原厂 Developer ID 签名或 Apple 公证。GUI 为 Intel x86_64，Apple Silicon 需要 Rosetta；尚未验证 macOS 实机刷写。

Mac 封包源码标签为 `p8-fix1-20261016-mac`；原固件发布标签和 Windows 附件保持不变。新 Mac 源码包包含完整固件及封包源码。请查看现有 Release 中专属 Mac 使用说明和验证附件。
