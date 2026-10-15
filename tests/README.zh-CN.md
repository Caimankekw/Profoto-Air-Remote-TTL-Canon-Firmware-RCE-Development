# 离线验证

在仓库根目录用 Python 3.9+ 执行；不需要 pip 依赖或连接设备：

```console
python -I -B tests/test_reference_codec.py -v
python -I -B tests/test_container.py --original "path/to/C11.exe" -v
python -I -B tests/test_build.py --original "path/to/C11.exe" -v
python -I -B tests/test_isolated_build.py --original "path/to/C11.exe"
```

前三组分别覆盖 7 项编码、13 项容器、13 项源码构建与边界测试。没有提供原厂输入时，
依赖它的测试会明确跳过。最后一组将源码依赖复制到新的临时目录，以 Python `-I`
运行；文件访问检查禁止读取复制目录、指定原厂 EXE 和 Python 安装目录以外的文件。
临时测试目录会保留，不自动删除。

这些检查验证源码与产物一致性及封装边界，不验证硬件行为。此前 P8 有界仿真验证的是
同一份冻结镜像；完整历史虚拟机和证据工作区不是构建依赖，本精简源码包不包含它们。
