# C11 地址变换参考数据

[English](README.md) | 简体中文

开发者：Caimankekw。工具源代码采用 AGPL-3.0-only。

`c11_offset_transform.bin` 是从已恢复的协议行为整理出的地址变换参数，不包含设备序列号、批次、日期、USB 路径、设备程序备份或原厂程序明文。它供离线工具在原 C11 更新器的传输字节与 MCU 字节之间转换。原厂固件和更新器的权利仍属于原权利人。

适用范围严格为 MCU 字节地址 `[0x4002, 0x10000)`。数据长度 73,725 字节，由 49,150 个 XOR 字节和 24,575 个打包掩码字节组成。掩码的低半字节对应较小地址，高半字节对应下一个地址。文件中没有文件头，范围、格式和 SHA-256 由 `codec_manifest.json` 及工具内置常量固定。

对每个地址，设原字节为 `p`、XOR 字节为 `k`、四位掩码为 `m`：

```text
t = (p XOR (p >> 4)) AND m AND 0x0F
swap(p, m) = p XOR t XOR (t << 4)
encode(p) = swap(p, m) XOR k
decode(c) = swap(c XOR k, m)
```

变换不会移动字节地址。每个掩码位决定是否交换同一字节中相隔四位的一对位；交换操作是自身的逆运算。映射由固定填充参考和固定指令字参考恢复，参考读取产生的设备信息及原始事务记录没有导出。

`tools/reference_codec.py` 只使用 Python 标准库。`ReferenceCodec().encode(address, plaintext)`、`decode(address, opaque)` 和 `encode_patch(address, plaintext)` 均拒绝范围外请求。

`decode_original_bytes()` 仅接受 SHA-256 固定的原 C11 完整应用传输区，返回以 `0x4000` 为基址的 113,664 字节明文占位镜像与已知字节掩码。`0x4000–0x4001` 仍未知，明文填零且掩码为零；这个零不能作为实际指令刷写。`0x10000–0x1FBFF` 是该固定 C11 的已确认 FF 填充，仅在完整原始传输区哈希吻合后补齐，不声称恢复了该区间的通用编码器。构建封装必须直接保留首字、尾部、稀疏间隙及配置的原始传输字节。

`codec_equivalence.json` 记录导出时与工作区原解码器逐地址比较的结果，以及原 C11 明文与掩码的哈希验证。运行 `python -B -m unittest discover -s tests -p test_reference_codec.py` 可执行不需要原厂文件的自检。参考数据的等价性不能代替实机启动、射频和灯具行为验证。
