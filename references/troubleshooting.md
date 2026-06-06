# Troubleshooting

## 缺少 API Key

复制 `.env.example` 为 `.env`，填写 `N2S_API_KEY`、`N2S_BASE_URL`、`N2S_MODEL`。无密钥时可使用 `--mock` 演示模式。

## 输入章节不足

输入文本至少需要 3 个章节标题，或 3 个明显段落块。

## YAML 校验失败

检查 `docs/yaml-schema.md`，尤其是 `episodes`、`scenes`、`elements.type` 和 `camera_note`。
