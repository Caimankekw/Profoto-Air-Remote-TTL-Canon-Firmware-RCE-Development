# AIR2-P8 Windows 外壳源码

[English](README.md) · Copyright (C) 2026 **Caimankekw** · **AGPL-3.0-only**

本目录为冻结的 AIR2-P8 GUI 构建精简 NSIS 自解压外壳，不修改固件、不实现另一个刷写器、不访问 USB，也不执行生成的更新器或安装器。许可范围和实验限制见根 LICENSE、NOTICE 及中英文免责声明。

项目源码：[P8 固件开发](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8) · [Windows 外壳](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8/windows) · [main 原始 C11 逆向](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main)。

交付包内的 `source.zip` 是本次封包精确对应的源码快照。`package_manifest.json` 记录其 SHA256，归档内 `source_manifest.json` 记录每项源码文件。分支可能继续更新；复现这一份安装包时应使用随包归档，不应假设当前 P8 分支始终保持原样。

## 输入与构建

Python 3.9 以上，仅需标准库。显式提供完整 NSIS 3.13 目录、7-Zip 26.04 x64 的 `7z.exe` 和同目录 `7z.dll`、AIR2-P8 GUI、原厂 C11 GUI，以及本项目最终对应源码 ZIP。[input_manifest.json](input_manifest.json) 固定更新器和工具指纹；源码 ZIP 通过必填 SHA256 参数固定，顶层目录必须为 `AirRemote_TTL_C_AIR2_P8/`，其中 `source_manifest.json` 记录其他每个文件。

```powershell
python windows/build_package.py `
  --updater "C:\inputs\AirRemote_TTL_C_C11_AIR2_P8_Caimankekw_EXPERIMENTAL.exe" `
  --original "C:\inputs\Air-Remote-TTL-C-Firmware-C11.exe" `
  --source-archive "C:\inputs\AirRemote_TTL_C_AIR2_P8-source.zip" `
  --source-sha256 "替换为源码ZIP的SHA256" `
  --nsis-dir "C:\tools\nsis-3.13" `
  --seven-zip "C:\tools\7zip\7z.exe" `
  --output "C:\output\AIR2-P8-new-build"
```

输出目录必须不存在；省略 `--output` 时在 `windows/build/` 下创建 UTC 时间戳目录。输入均显式指定，不搜索私人开发目录、不自动下载。脚本校验整个 NSIS 目录，需提供未改动的完整发行包。

源码树和根文档定稿后再生成源码 ZIP。ZIP 包含本目录，排除 `build/`、`dist/`、缓存及生成的发布文件。构建器校验 ZIP 每项与清单一致，并核对归档中的 Windows 源码、根许可文档与当前字节相同。生成源码 ZIP 后不要再改源码然后直接封装。

## 输出与检查

输出包括 `Profoto-AirRemote-TTL-C-AIR2-P8-Custom-Updater.exe`、便携 ZIP、解压内容、日志、SHA256SUMS 和 `package_verification.json`。实际用户内容仅为 P8/原厂恢复 GUI、对应 source.zip、使用说明、许可、免责声明和清单，不含 HSS-P3 或其他开发固件。

向导提供中英免责声明和 AGPL 页面，解压到尚不存在的新目录；“打开更新器”默认不勾选。不静默更新、不安装驱动、不删除文件、不增加卸载流程。内部 GUI 保持冻结 SHA256：`dec0660b9568713d36a13e44909741b2891d30680895f0ef3406a31e9cbebde1`。

构建仅运行显式提供的编译器和静态解包工具；检查 PE 身份和权限、源码 ZIP、便携 ZIP、每项安装器解包字节及额外 NSIS 插件。外壳未签名，不承诺外层 EXE 每次重建同哈希；内部更新器及所有用户文件必须逐字节一致。静态检查不代替真机或 Windows 界面实测。

运行离线辅助测试：`python -B windows/test_build_package.py`。`installer.nsi` 和两份使用说明模板是界面源码；构建为 NSIS 生成 UTF-16 免责声明/许可显示副本，用户目录仍保留原 UTF-8 文件。未修改的 NSIS 许可正文位于 `vendor/NSIS-COPYING.txt`。
