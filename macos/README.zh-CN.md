# 原生 macOS 封包

开发者：**Caimankekw**。原创源码采用 AGPL-3.0-only。许可范围与限制见根目录的
LICENSE、NOTICE.zh-CN.md 和 DISCLAIMER.zh-CN.md。

此层将已审查的固件封装进对应型号的原厂 macOS 更新器，不修改相机、HSS、无线或
AIR2 逻辑。传输 HEX 从已发布且固定哈希的 Windows 更新器中提取，同一发布版的
Mac 与 Windows HEX 完全一致。

`model.json` 固定型号、原厂 Mac ZIP、Windows 便携包、成员路径及原厂应用资源哈希。
完整对应源码 ZIP 的 SHA256 由构建参数独立提供，避免自引用哈希；逐文件核对清单、
归档与指定 Git 提交的干净检出内容。

## 构建

需 macOS 11 或更新版本、Python 3.9+、Git 和系统自带的 `hdiutil`、`ditto`、
`codesign`。GitHub 工作流使用 `macos-15-intel`，全程不执行更新器。

```sh
python3 -B -m unittest discover -s macos -p 'test_*.py' -v
python3 -B macos/build_package.py \
  --stock-maczip /path/to/pinned-stock-mac.zip \
  --windows-package /path/to/pinned-windows-portable.zip \
  --source-archive /path/to/corresponding-source.zip \
  --source-sha256 VERIFIED_SOURCE_SHA256 \
  --source-commit FULL_GIT_COMMIT \
  --output /path/to/new-output-directory
```

输出目录必须是新目录。构建中间件和候选应用均保留，不删除已有文件。源码检出需
保持干净；下载输入和生成结果应放在源码目录之外。

## 原厂行为与签名

原厂磁盘镜像只读挂载，通过 `ditto` 复制应用，仅替换固件资源。Info.plist、helper、
UI 资源、执行权限和其他资源均必须保持一致。应用内部保留原厂名称；自定义版本及
开发者署名在外层 DMG 和配套说明中标明。

替换资源后原厂外层签名不再有效，因此只对外层应用进行 ad-hoc 签名，不使用
`--deep` 重签，保留 helper 原字节及签名。对主程序比较时只归一化嵌入签名及其
分配信息，程序代码和其余链接数据不得改变。必须通过 `codesign --verify --deep
--strict`、原生 DMG 挂载和最终全量回读检查。

自定义应用没有 Developer ID 签名或公证。ad-hoc 签名有效不等于 Gatekeeper 已放行，
也不保证原厂 GUI 可在所有 Mac 上运行。x86_64 GUI 在 Apple Silicon 上可能需要
Rosetta 2。此构建没有验证实机启动、USB 刷写或拍摄行为。

最终 ZIP 包含自定义 APFS/UDZO DMG、未改动的原厂恢复 DMG、厂商 FAQ/许可、双语说明与
免责声明、AGPL 许可、完整对应源码、SHA256 清单及静态验证报告。恢复不保证成功。
CI 只有仓库只读权限，只上传构建产物，发布需另行检查。
