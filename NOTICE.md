# License scope / 许可范围

Copyright (C) 2026 Caimankekw.

Repository / 项目仓库: https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development

The `P8` branch contains the corresponding authored development source; `main` contains analysis of unmodified C11. Release notes pin the exact commits, and each Windows package includes its corresponding `source.zip`.

`P8` 分支提供对应原创开发源码，`main` 提供原版 C11 逆向材料。Release 说明固定到具体源码提交，每份 Windows 包同时包含对应 `source.zip`。

## English

Caimankekw's original patch generators, integration and packaging tools, tests, and explanatory documentation are licensed under **AGPL-3.0-only**. See the complete, unmodified [LICENSE](LICENSE). The corresponding authored source is included in the source archive distributed with the Windows package.

This grant applies only to material for which the developer can grant rights. Original Profoto firmware, copied or relocated original instructions, firmware resources, the original updater and loader, trademarks, and other third-party material retain their respective rights. Recovered logic and reference parameters document observations of that firmware; including them does not grant additional rights to the original software. The mixed generated firmware/updater is not represented as wholly authored by Caimankekw or wholly relicensed under AGPL.

The source distribution excludes the original vendor EXE, device readbacks, USB captures, individual device configuration/identifiers and account data. The original EXE is a separately supplied, hash-checked build input; the Windows distribution includes an unmodified original recovery EXE. Reusing the vendor GUI or container does not imply approval or a valid vendor signature.

NSIS, its runtime/plugins and 7-Zip keep their own licenses. The Windows build retains the NSIS copyright/license notice with its distributed runtime; 7-Zip is used as a separately supplied build verification tool. See `windows/` for inputs and packaging source. The project license and disclaimers do not limit rights granted by the applicable open-source licenses or non-excludable statutory rights.

## 简体中文

Caimankekw 原创的补丁生成器、整合与打包工具、测试及解释文档采用 **AGPL-3.0-only**。完整、未经修改的协议见 [LICENSE](LICENSE)。Windows 包附带的源码压缩包提供对应原创源码。

授权仅涵盖开发者有权许可的内容。原厂 Profoto 固件、复制或重定位的原始指令、固件资源、原厂更新器和 loader、商标及其他第三方材料保留各自权利。恢复逻辑和参考参数记录对固件的观察，收录它们不授予额外原厂软件权利。生成的混合固件和更新器不宣称全部由 Caimankekw 创作或已整体改为 AGPL。

源码包不包含原厂 EXE、设备读回、USB 采集、设备个体配置/身份或账号资料。原厂 EXE 是用户单独提供并经哈希核验的构建输入；Windows 包附带未修改的原厂恢复 EXE。沿用原厂 GUI 或容器不代表原厂认可或具有有效原厂签名。

NSIS、其运行组件/插件及 7-Zip 保留各自许可。Windows 包随 NSIS 运行组件保留其版权/许可说明；7-Zip 作为用户另备的构建验证工具。输入要求及打包源码见 `windows/`。本项目协议和免责声明不缩减适用开源协议授予的权利或法律不得排除的权利。
