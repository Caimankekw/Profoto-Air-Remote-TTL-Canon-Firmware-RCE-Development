# 离线验证

[English](README.md) | 简体中文

在仓库根目录用 Python 3.9+ 执行；不需要 pip 依赖或连接设备：

```console
python -I -B tests/test_reference_codec.py -v
python -I -B tests/test_container.py --original "path/to/C11.exe" -v
python -I -B tests/test_build.py --original "path/to/C11.exe" -v
python -I -B tests/test_isolated_build.py --original "path/to/C11.exe"
```

前三组分别覆盖 7 项编码、13 项容器、13 项源码构建与边界测试。未提供原厂输入时，依赖该输入的测试会明确跳过。最后一组将源码依赖复制到新的临时目录，以 Python `-I` 运行；文件访问检查禁止读取复制目录、指定原厂 EXE 和 Python 安装目录以外的文件。临时目录会保留。原厂更新器仅作为数据读取，不会执行；测试不访问 USB。

[VERIFICATION.json](VERIFICATION.json) 分开保存两份记录：

- `current_fix1.frozen_candidate_report` 是冻结 FIX1 发布验证报告的完整副本。其中源码包哈希标识此前的 35 文件输入 ZIP，并非本次新整合的发布源码 ZIP。固件和更新器哈希将报告结果绑定到 FIX1。
- `historical_p8.report` 原样保存旧 P8 独立验证。其哈希、源码清单和通过结果属于 P8，不证明 FIX1 或新封包通过检查。

冻结 FIX1 报告记录 UI 470 项、无线 1,944 项、持久化 717 项、整合 333 项、原生空闲到期 77 项，以及上述 33 项独立检查和隔离重建。77 项到期检查包含 24 项冻结 P8 失败对照。开发专用的 `verify_idle_expiry.py` 和完整行为回归需要原逆向开发工作区，不包含在本精简源码 ZIP 中。报告指纹用于保存证据身份，并不表示本包包含这些回放工具。

FIX1 尚未进行实机启动或相机测试。回放采用有边界的时钟、UART、Flash 和 LCD 模型，并非完整 MCU／ISR 或物理射频模型。这些检查不能证明硬件启动、物理按键速率、射频接收、曝光或掉电行为。HSS-P3 字节保持不变；旧 P8 的 HSS 总数不代表本次重新执行的 FIX1 HSS 回放或实机测量。
