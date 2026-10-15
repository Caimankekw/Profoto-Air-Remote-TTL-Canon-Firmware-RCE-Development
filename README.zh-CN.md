# Profoto Air Remote TTL Canon Firmware RCE Development

[English](README.md) | 开发者：**Caimankekw**

`main` 仅收录**未修改的 Air Remote TTL-C C11 应用程序**逆向说明与离线分析工具，不含固件镜像、更新器 EXE、设备采集、USB 写入工具或 AIR2 补丁生成器。研究未修改的原程序，不等于已经恢复全部源码：这里的逻辑解释是人工整理的局部模型，明确不可直接编译。

| 位置 | 用途 |
|---|---|
| `main` | 原 C11 分析、地址索引及可复现的数值 PIC18 候选反汇编工具 |
| [P8 分支](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8) | AIR2-P8 实验开发源码、验证与 Windows 封包工具 |
| [Releases](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases) | 单独发布的 AIR2-P8 实验包；使用时阅读对应 P8 文档 |

AIR2-P8 是非官方实验修改。离线检查不代表完整硬件兼容、射频时序或光学 HSS 效果已获验证。`main` 不提供安装或刷写流程，参见[免责声明](DISCLAIMER.zh-CN.md)。

## 分析原 C11

使用 **Python 3.9 或更新版本**及标准库，无需 `pip` 依赖、Ghidra 或编译器。按 [inputs/README.zh-CN.md](inputs/README.zh-CN.md) 自行提供原厂 Windows C11 更新器。工具只把 EXE 当作数据读取，不运行 EXE，不连接设备。

在仓库根目录运行：

```powershell
python -I -B tools/disassemble.py --original "C:\path\to\Air-Remote-TTL-C-Firmware-C11.exe" --out build/original_C11.listing.txt
python -I -B -m unittest discover -s tests -p test_reference_codec.py
```

支持的更新器大小为 **3,938,448 字节**，SHA-256 为 `e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240`；其他输入会被拒绝。默认反汇编区间为 PIC18 **字节地址** `[0x4002, 0x9780)`，可用 `--start` / `--end` 指定 `[0x4002, 0x10000]` 内的偶数边界。已有且内容不同的输出不会被覆盖。

输出是线性指令候选列表，不证明所有条目都可达，也不是完整的代码/数据分离。`0x4000–0x4001` 首个明文字仍未知，因此不进入列表。变换参数的已确认范围与仅适用于固定原程序的尾部重建，见 [reference/README.zh-CN.md](reference/README.zh-CN.md)。

## 内容

- [C11/](C11/README.zh-CN.md)：原按键扫描、TTL/MAN 数据银行、无线请求接口、相机/HSS 边界与存储索引；C 风格说明不是厂商源码。
- `tools/`：四个仅依赖标准库的模块，负责严格解析原容器、字节变换及候选反汇编。文档中的入口只写指定文本列表。
- [reference/](reference/README.zh-CN.md)：派生地址变换参数、格式清单与已有等价性记录，不是设备备份或固件镜像。
- `tests/`：无需原厂 EXE 或设备的 codec 自检。

运行依赖闭包只有 `tools/` 内四个文件，以及 `reference/codec_manifest.json`、`reference/c11_offset_transform.bin`。保持 `tools/` 与 `reference/` 同级即可。通用 codec/container 模块也暴露内存变换辅助接口，但这里不包含 P8 hook、策略补丁或固件构建入口。

## 权利范围

Caimankekw 原创解释、工具与测试采用 [AGPL-3.0-only](LICENSE)。原固件、恢复的原指令、厂商资源及第三方材料保留各自权利，本项目不将其重新许可。详见 [NOTICE.md](NOTICE.md)。本项目不暗示官方关联、认可或保证。
