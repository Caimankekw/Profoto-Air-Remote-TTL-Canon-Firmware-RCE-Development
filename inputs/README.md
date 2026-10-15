# Official input / 原厂输入

[简体中文](README.zh-CN.md)

Supply your own unmodified **Air-Remote-TTL-C-Firmware-C11.exe** with SHA-256:

`e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240`

The build accepts this EXE through `--original`; it may be outside this directory.
It is parsed as data and is never executed. No device backup, configuration,
serial number, login information, or USB capture is needed. Do not commit the
vendor EXE or generated vendor-derived images to the source repository.

请自行提供上述散列的原厂 Windows C11 更新器，通过 `--original` 显式指定。
构建只读取其内嵌固件，不运行 EXE、不访问设备。无需设备备份、配置、序列号、
账号或 USB 采集记录。原厂更新器及生成的原厂衍生镜像不属于本项目原创源码。

From the repository root / 在仓库根目录执行：

```console
python -B build.py --original "path/to/Air-Remote-TTL-C-Firmware-C11.exe"
```
