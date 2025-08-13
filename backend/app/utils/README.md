# Lighthouse Parser Test Setup

这个文件夹包含了测试 Lighthouse Parser 的完整环境。

## 📁 文件说明

- `test_seo_page.html` - 包含各种 SEO 问题的测试 HTML 文件
- `test_lighthouse_parser.py` - 测试脚本，会调用 Lighthouse 服务并运行 parser
- `README.md` - 这个说明文件

## 🚀 使用方法

### 1. 启动 Lighthouse 服务

```bash
# 在另一个终端窗口
cd ../../lighthouse-service
node server.js
```

### 2. 运行测试

```bash
# 在 utils 文件夹中
cd app/utils
python3 test_lighthouse_parser.py
```

## 🔄 测试流程

1. **读取 HTML**: 脚本读取 `test_seo_page.html` 文件
2. **调用 Lighthouse**: 将 HTML 发送到 Lighthouse 服务进行分析
3. **运行 Parser**: 用你的 `LHRTool` 解析 Lighthouse 返回的结果
4. **生成报告**: 创建一个详细的 JSON 报告文件，方便你手动检查

## 📊 输出结果

- **控制台输出**: 显示测试进度和结果摘要
- **JSON 报告**: 包含完整的 Lighthouse 原始数据和解析后的结果
- **文件名格式**: `lighthouse_parser_test_result_YYYYMMDD_HHMMSS.json`

## 🐛 故障排除

如果遇到问题：

1. 确保 Lighthouse 服务在运行 (端口 3001)
2. 检查 HTML 文件是否存在
3. 确保安装了 `requests` 库: `pip install requests`

## 💡 自定义测试

你可以：

- 修改 `test_seo_page.html` 来测试不同的 SEO 问题
- 调整 `test_lighthouse_parser.py` 中的 Lighthouse 服务 URL
- 修改报告格式来满足你的需求
