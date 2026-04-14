# ReadEcho Pro EXE 自动更新工具

## 功能说明
`update_exe.bat` 是一个自动化的批处理工具，用于在更新主程序 `ReadEcho_Pro.py` 后，自动重新打包生成可执行文件 (EXE)。

## 使用方法
1. 更新你的 `ReadEcho_Pro.py` 文件
2. 双击运行 `update_exe.bat`
3. 等待打包完成（可能需要几分钟）
4. 新的EXE文件会在 `dist\ReadEcho_Pro\` 目录中生成

## 工具执行步骤
1. **清理旧文件**：删除旧的 `build`、`dist` 目录和 `ReadEcho_Pro.spec` 文件
2. **激活环境**：激活 `venv_ai` 虚拟环境
3. **重新打包**：使用 PyInstaller 生成新的 EXE 文件
4. **创建启动器**：生成 `ReadEcho_Pro_Exe.bat` 启动文件

## 文件结构
```
ReadEcho/
├── ReadEcho_Pro.py          # 主程序文件
├── update_exe.bat           # 自动更新工具
├── ReadEcho_Pro_Exe.bat     # EXE启动器（自动生成）
├── EXE_Update_README.md     # EXE更新工具使用说明
├── readme.txt               # 项目说明文档
├── start.bat                # 原始启动脚本
├── log.txt                  # 程序运行日志
├── readecho.db              # 数据库文件（书籍摘要）
├── readecho_v1.db           # 数据库文件（笔记）
├── temp_note.wav            # 临时音频文件
├── ReadEcho_Pro.spec        # PyInstaller配置文件（自动生成）
├── .gitignore               # Git忽略文件配置
├── venv_ai/                 # Python虚拟环境
├── .venv/                   # 另一个Python虚拟环境
├── dist/                    # 生成的EXE目录（自动生成）
│   └── ReadEcho_Pro/
│       ├── ReadEcho_Pro.exe
│       └── _internal/
├── build/                   # 构建临时文件（自动生成）
└── .git/                    # Git版本控制目录
```

## 注意事项
- 确保 `venv_ai` 虚拟环境存在且包含所有必要的依赖
- 打包过程可能需要几分钟时间，请耐心等待
- 生成的EXE文件包含所有依赖，大小可能较大（几百MB）
- 如果打包失败，请检查虚拟环境和依赖是否正确安装

## 故障排除
- 如果提示 "venv_ai 虚拟环境未找到"，请确保虚拟环境存在
- 如果提示 "ReadEcho_Pro.py 未找到"，请确保主程序文件存在
- 如果 PyInstaller 失败，请检查虚拟环境中是否安装了 PyInstaller