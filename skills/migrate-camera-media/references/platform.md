# macOS、exFAT 与 Sony

## 协商速率与连接

- 用 `diskutil info -plist` 读取卷 UUID；该输出包含 `MountPoint`，不保证有 `Mounted` 字段。查询挂载根，不把任意项目子目录直接传给 `diskutil info`。
- USB 链路速率是 bit/s，传输报告一般是 byte/s。5 Gb/s、10 Gb/s 都不是实际文件复制速度；读卡、编码哈希、SSD 和 USB 共享带宽都可能限速。
- 雷电线不会让 USB 相机变成雷电设备；读取实际 `UsbLinkSpeed`。不要通过多个进程争抢同一张卡来测速。
- FX3A 官方连接流程是 USB-C 接电脑、选择 MassStorage(MSC)，支持 SuperSpeed USB 5 Gb/s。相机和 SSD 分别接电脑，数据可直接从卡写 SSD，无需先落电脑内部磁盘。
- FX3A 的菜单 Copy 是双卡槽间复制；它没有文档支持的 USB SSD 直连卸卡功能。核对具体型号，不将此结论推广至其他设备。

## 文件完整性

- Sony 的整卡原样归档应同时保留 DCIM、M4ROOT、PRIVATE、AVF_INFO、SONY 及它们的关联文件。不要只取 MP4，也不要扁平化文件名。
- RSV 可能表示写入未完成或管理信息异常。将其原样复制、核验并明确标记“未恢复”，不要当作无用临时文件删除，也不要把改后缀当恢复。
- exFAT 在 macOS 上可能自动生成 AppleDouble `._` 元数据文件。只把“源清单没有、存在对应真实文件/目录、头部为 0x00051607 和版本 0x00020000”的额外文件单独登记；不要忽略所有未知额外文件。
- `os.listxattr` 不一定存在于 macOS Python。转存工具预先导入 `xattr`，避免部分复制后才失败。媒体抽查从源清单选择路径，不用扩展名 glob 扫到 AppleDouble。
- `F_NOCACHE=48` 用于文件数据缓存策略；`F_FULLFSYNC=51` 请求持久化刷新。先正常 `fsync`；仅对明确“不支持”的 errno 记录兼容限制，EIO 等必须报错。不要把成功调用或回读解释为硬件永久落盘保证。
- 以文件逻辑字节数核验数据量，不以不同分配单元下的 `du` 相等为标准。

## 官方依据

以下页面在 2026-09-06 核对过；涉及不同型号或固件变化时重新确认。

- [FX3A：连接电脑](https://helpguide.sony.net/ilc/2510/v1/en/contents/0903_connection_pc.html)
- [FX3A：USB 连接模式](https://helpguide.sony.net/ilc/2510/v1/en/contents/0601_usb_connection.html)
- [FX3A：导入影像及电脑删除注意事项](https://helpguide.sony.net/ilc/2510/v1/en/contents/0903B_import_pc_win.html)
- [Sony：RSV 无法播放及修复局限](https://support.sony.jp/electronics/support/articles/00375062)
- [Sony Catalyst：关联文件与复制核验](https://helpguide.sony.net/di-app/cp/v1/en/Content/Library_import.htm)
- [Pomfort：源与目标验证、MHL](https://kb.pomfort.com/silverstack/reference/workflow-configuration/workflow-activities/)
- [CISA：3-2-1 备份](https://www.cisa.gov/sites/default/files/publications/data_backup_options.pdf)
