# Air Remote TTL-C · AIR2-P8

[English](README.md) | 简体中文

开发者：[Caimankekw](https://github.com/Caimankekw) · 原创代码：[AGPL-3.0-only](LICENSE)

面向 **Profoto Air Remote TTL-C（Canon）C11** 的非官方实验固件。此工程从源码生成当前 AIR2-P8，再封装进原 C11 图形更新器。它是逆向分析和二进制补丁工程，不是厂商完整 C 源码，也不适用于 Connect、Connect Pro 或其他卡口型号。

按 B10 REV5 的方式，源码工程与 Windows 安装包分开整理；只保留当前版本所需材料。构建不要求旧开发工作区或任何中间版固件。

这是 [Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development) 的 **P8 开发分支**。[main 分支](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main) 仅提供未修改 C11 固件的逆向材料及离线分析工具。Windows 包与对应源码见 [Releases](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases)，发布说明标明对应源码提交和文件哈希。

## 功能与操作

- MAN-AIR1：相对功率调节；仅调节后临时显示数字。
- MAN-AIR2：按引闪器显示的绝对目标调节灯；当前页已启用的三组功率常驻显示。
- **C＋HEAD**：在 ABC / DEF 页间切换，适用于 TTL 和两个手动模式。
- **C＋MODEL**：MAN 中切 AIR1 / AIR2；TTL 中忽略该组合，保留上次手动类型。
- A、B、加减键不进入组合等待，保留正常短按及长按步进。
- MODE 在 TTL / MAN 之间切换，返回 MAN 时恢复上次 AIR1 / AIR2。
- ALL 作用于六组；记忆六组 AIR2 目标、闪光和造型灯开关、页面及模式。
- 保留已有 HSS-P3 路径。

**TTL 中 ABC 是曝光补偿，DEF 按记住的手动类型控制，不是六组自动 TTL。** 固定液晶的 ABC 字母不能改为 DEF；DEF 页熄灭 ABC 行标，切页时短暂提示 d/E/F。

只有 C、HEAD、MODEL 等待组合确认。单独操作这些键可能稍有等待；组合生效后需全部松开。原加减双按和 A＋减号不再是快捷键，按原扫描优先级处理。原同步发送、保存及扫描限制仍在，不能保证任意速度连按都被接受；忙时本轮可能被拒绝，不会排队补发。

AIR2 目标范围为 0.1–10.0，但灯具自身的最低输出可能更高。显示值是引闪器目标，不是灯端实时回读。首次安装或旧记录迁移时 DEF 默认关闭、目标 5.0。重新安装可能重置新增参数。

## 目录

| 路径 | 内容 |
| --- | --- |
| [C11](C11/README.zh-CN.md) | 精简的原 C11 逆向说明和恢复逻辑 |
| `source/` | UI、六组无线、持久化、HSS 补丁与链接代码 |
| `tools/` | 固件容器、编码、反汇编、重建和源码打包工具 |
| `reference/` | 解码所需的通用地址变换参数及指纹；不含设备备份 |
| [windows](windows/README.zh-CN.md) | Windows 自解压安装包构建源码 |
| `tests/` | 独立构建与输入边界测试 |
| [inputs](inputs/README.md) | 用户自备原厂输入的要求；原厂 EXE 不进入源码包 |

## 从源码构建

Python **3.9 或更新版本**，固件构建使用标准库，不需要安装 Python 第三方包。准备原厂 `Air-Remote-TTL-C-Firmware-C11.exe`，从工程根目录执行：

```powershell
python -B build.py --original "inputs\Air-Remote-TTL-C-Firmware-C11.exe"
```

原厂 EXE 的 SHA-256 必须为：

```text
e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240
```

构建从原厂 EXE 解码，执行 HSS 和 AIR2 的源码生成器、链接、CRC 与编码检查，再输出 `build/`。不会运行更新器或访问 USB。公开源码包不包含原厂 EXE；可使用 Windows 包中未修改的原厂恢复 EXE。

本版本必须重现以下固定文件：

```text
AIR2-P8.base4000.partial.bin
337120c7ed51954f4cdf0e60816e0289583a3c6b4ad400504d0cbef0a259f185

AirRemote_TTL_C_C11_AIR2_P8_Caimankekw_EXPERIMENTAL.exe
dec0660b9568713d36a13e44909741b2891d30680895f0ef3406a31e9cbebde1
```

分析 BIN 的首两个明文字节仍未知，**不能直接刷写**。正常安装使用 EXE 图形界面。EXE 重建会保留原厂 GUI、loader、未知首字和稀疏尾部；修改固件资源后，原厂签名不再有效。

## Windows 包

`Profoto-AirRemote-TTL-C-AIR2-P8-Custom-Updater.exe` 沿用 REV5 的 NSIS 自解压形式，包含当前更新器、原厂恢复程序、双语说明、许可、免责声明及对应源码包。外壳解压至用户目录；完成页可选择打开图形更新器，刷写仍需在更新器中操作。

无需 Python 即可使用该包。构建外壳需 NSIS 和 7-Zip，具体固定版本与命令见 [Windows 构建说明](windows/README.zh-CN.md)。源码打包命令为 `python -B tools/package_source.py`，输出在 `dist/`。

## 验证范围

冻结 P8 镜像已通过 UI 470 项、无线 1,944 项、持久化 717 项、整合 333 项，以及 HSS 966,339 项和 576 组序列的离线检查。本次精简工程另检查源码构建、容器回环、固定输出指纹和安装包解包内容；这些检查不代替实机启动、射频接收、曝光或掉电验证。

安装后优先检查：连续加号五次增加 0.5、减号五次恢复；两种组合均不额外改变闪光或造型灯开关；模式和参数保存后重启正常。屏幕正确与灯端执行应分别确认。若异常，使用随包原厂恢复 GUI；恢复程序不构成可恢复性保证。

使用前阅读[中文免责声明](DISCLAIMER.zh-CN.md)或[英文免责声明](DISCLAIMER.md)。[NOTICE](NOTICE.md)区分原创代码、原厂材料和第三方组件的许可；不将混合二进制整体重新授权为 AGPL。
