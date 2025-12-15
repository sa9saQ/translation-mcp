# DeepL Translation MCP Server

DeepL APIを使用した翻訳MCPサーバー。Claude Desktopから高品質な翻訳機能を利用できます。

## 機能

- **translate** - テキスト翻訳（30+言語対応）
- **get_supported_languages** - 対応言語一覧の取得
- **get_usage** - API使用量の確認
- **detect_language** - 言語検出

## 必要要件

- Python 3.10以上
- [uv](https://docs.astral.sh/uv/)（推奨）または pip
- DeepL APIキー（[DeepL API](https://www.deepl.com/pro-api)から取得）

## インストール

### uv を使用（推奨）

```bash
cd /path/to/翻訳MCP
uv sync
```

### pip を使用

```bash
cd /path/to/翻訳MCP
pip install -e .
```

## Claude Desktop 設定

`%APPDATA%\Claude\claude_desktop_config.json`（Windows）または
`~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）に以下を追加：

```json
{
  "mcpServers": {
    "deepl": {
      "command": "uv",
      "args": [
        "--directory",
        "D:\\プロジェクト\\MCP\\翻訳MCP",
        "run",
        "deepl-mcp"
      ],
      "env": {
        "DEEPL_API_KEY": "your-deepl-api-key-here"
      }
    }
  }
}
```

**注意**: `DEEPL_API_KEY` を実際のAPIキーに置き換えてください。

## 使用例

Claude Desktopで以下のように使用できます：

### テキスト翻訳

```
「Hello, how are you today?」を日本語に翻訳して
```

```
Translate "こんにちは" to English
```

### フォーマリティ指定

```
「Thank you for your help」を日本語に丁寧に翻訳して
```

### 対応言語の確認

```
DeepLで対応している言語を教えて
```

### API使用量の確認

```
DeepL APIの使用量を確認して
```

## ツール詳細

### translate

| パラメータ | 必須 | 説明 |
|-----------|------|------|
| text | Yes | 翻訳するテキスト |
| target_lang | Yes | 翻訳先言語（例: `Japanese`, `JA`, `EN-US`） |
| source_lang | No | 翻訳元言語（省略時は自動検出） |
| formality | No | フォーマリティ: `more`, `less`, `prefer_more`, `prefer_less` |
| preserve_formatting | No | フォーマット保持（デフォルト: true） |

### 対応言語コード

言語名でも言語コードでも指定可能：

- `Japanese` または `JA`
- `English` または `EN-US` / `EN-GB`
- `German` または `DE`
- `French` または `FR`
- `Chinese` または `ZH-HANS` / `ZH-HANT`
- など

## 開発

### テスト実行

```bash
uv run python -c "from deepl_mcp.server import get_translator; print('OK')"
```

### サーバー単体起動

```bash
export DEEPL_API_KEY="your-api-key"
uv run deepl-mcp
```

## ライセンス

MIT License
