# 更新记录

[English](CHANGELOG.md) | 简体中文

## 2026-10-16 · AIR2-P8-FIX1

发布标签：`p8-fix1-20261016`。开发者：Caimankekw。

- 修复 AIR1 相对值到期时无线发送、相机模式请求或旧发送事务正忙导致期限丢失的问题。忙时保留已到期的原生期限，恢复就绪后通过一次准备状态检查，同步完成期限消费与六组相对值清理。
- 未增加 RAM 或调整定时周期。AIR2 常驻目标、TTL ABC 曝光补偿、六组状态、页面与模式记忆保持原实现。无线、持久化组件及 HSS-P3 保护区与 P8 逐字节相同。
- 冻结离线证据记录 77 项原生期限用例，含 24 项旧 P8 失败对照；UI 470 项、无线 1,944 项、持久化 717 项、整合 333 项回归；构建 13 项、容器 13 项、编码 7 项检查和隔离源码重建。[验证记录](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/blob/p8-fix1-20261016/tests/VERIFICATION.json) 保存完整 FIX1 报告，并单独保留旧 P8 历史。
- 整合 Windows NSIS 外壳、便携 ZIP、对应源码、原厂 C11 分析资料和双语文档。本次发布源码 ZIP 区别于此前冻结 FIX1 输入 ZIP；固件与更新器哈希仍保持固定。
- **FIX1 尚未进行实机启动或相机测试。** 有界离线回放不能证明射频接收、曝光、物理按键速率或新的 HSS 实测结果。现有 P8 用户需下载 FIX1 更新器，先读[免责声明](DISCLAIMER.zh-CN.md)，再在图形界面中手动更新。

固件 SHA-256：`a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8`。

图形更新器 SHA-256：`f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed`。

## 2026-10-15 · AIR2-P8

历史发布：[p8-20261015](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases/tag/p8-20261015)。

- 发布 P8 六组 AIR1／AIR2 开发源码与 Windows 包，包括 C＋HEAD 翻页、C＋MODEL 切换手动类型，目标／开关／页面／模式记忆，以及既有 HSS-P3 路径。
- 历史离线证据覆盖 UI 470 项、无线 1,944 项、持久化 717 项、整合 333 项，以及 HSS 966,339 项和 576 组 HSS 序列。这些 HSS 总数属于旧 P8 证据，不是本次重新执行的 FIX1 测试。
- 旧独立构建验证完整保留在 [tests/VERIFICATION.json](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/blob/p8-fix1-20261016/tests/VERIFICATION.json) 的 `historical_p8` 字段中；其 P8 哈希与源码清单不代表新的 FIX1 发布。

历史固件 SHA-256：`337120c7ed51954f4cdf0e60816e0289583a3c6b4ad400504d0cbef0a259f185`。

历史图形更新器 SHA-256：`dec0660b9568713d36a13e44909741b2891d30680895f0ef3406a31e9cbebde1`。

同一验证记录也包含在随包的 Source.zip 内，路径为 tests/VERIFICATION.json。
