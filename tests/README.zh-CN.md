# 离线分析工具检查

[English](README.md)

在仓库根目录使用 Python 3.9+ 运行，无需第三方包或设备：

```powershell
python -I -B tests/test_reference_codec.py -v
python -I -B tests/test_container.py -v
python -I -B tests/test_container.py --original "C:\path\to\Air-Remote-TTL-C-Firmware-C11.exe" -v
```

codec 套件有 7 项测试。container 套件有 9 项纯内存测试及 4 项可选原厂输入测试；未传入 `--original` 时，后 4 项会明确跳过。合成修改仅在内存中进行，不写出或执行 EXE。测试验证解析、输入指纹、格式保留及变换边界，不证明设备启动或射频行为。

[根 README](../README.zh-CN.md) 的反汇编命令用于单独的端到端分析检查。生成列表不应提交到版本库，`main` 不依赖 P8 固件构建或仿真测试套件。
