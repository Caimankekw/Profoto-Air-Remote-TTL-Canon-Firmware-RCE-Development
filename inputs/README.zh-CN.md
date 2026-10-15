# 原厂构建输入

[English](README.md) | 简体中文

请自行提供未经修改的 **Air-Remote-TTL-C-Firmware-C11.exe**，SHA-256 必须为：

```text
e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240
```

在 P8 仓库根目录执行：

```powershell
python -B build.py --original "inputs\Air-Remote-TTL-C-Firmware-C11.exe"
```

也可通过 `--original` 指定目录外的文件。构建只将原厂 EXE 作为数据解析，不运行它、不访问 USB。Windows 发布包内未修改的原厂恢复 EXE 可作为该输入。

无需设备备份、个体配置、序列号、登录信息或 USB 采集。不要把原厂 EXE 或生成的固件镜像提交到源码仓库。原创工具采用 AGPL-3.0-only，原厂固件和更新器保留其原有权利，详见根目录 [NOTICE](../NOTICE.md)。
