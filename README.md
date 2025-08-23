# SpriteDefiner

Pyxel用のスプライト定義ダイアログシステム

## 概要

このプロジェクトは、Pyxelゲーム開発において、スプライトの定義や管理を効率化するためのダイアログベースのツールです。JSON駆動のレイアウトシステムと、ファイルシステム連携機能を提供します。

## 主要機能

- **JSON駆動ダイアログシステム**: dialogs.jsonでUIを定義
- **ファイルオープン/保存ダイアログ**: リアルファイルシステム連携
- **動的フィルターシステム**: 拡張子による自動ファイルフィルタリング
- **カスタムウィジェット**: TextBox、ListBox、Dropdown、Button等
- **イベントドリブン**: hasattr()パターンによる疎結合設計

## ファイル構成

```
SpriteDefiner/
├── SpriteDefiner.py          # メインアプリケーション
├── SpriteDefinerDlg/         # ダイアログシステム
│   ├── dialog_manager.py     # ダイアログ管理
│   ├── widgets.py            # UIウィジェット
│   ├── file_open_dialog.py   # ファイルオープン機能
│   ├── file_utils.py         # ファイルシステム操作
│   ├── dialogs.json          # UIレイアウト定義
│   └── ...
├── sprites.json              # スプライト定義データ
└── my_resource.pyxres        # Pyxelリソースファイル
```

## 技術仕様

- **言語**: Python 3.x
- **フレームワーク**: Pyxel
- **設計パターン**: MVC、イベントドリブン
- **設定**: JSON駆動レイアウト

## セットアップ

1. 依存関係のインストール:
```bash
pip install pyxel
```

2. アプリケーション実行:
```bash
python SpriteDefiner.py
```

## 使用方法

### ダイアログ表示
- **F1**: メインダイアログ
- **F2**: ファイルオープンダイアログ
- **F3**: ファイル保存ダイアログ
- **TAB**: クリックモード切り替え
- **Q**: 終了

### ファイルフィルター
dialogs.jsonでフィルター定義を変更可能:
```json
{
  "items": ["Pyxel Resource (*.pyxres)", "All Files (*.*)", "Image Files (*.png,*.jpg)"]
}
```

## 開発

### 最近のアップデート
- フィルターマッピングの重複コード削除（詳細: `_FileOpenDlg_refact.md`）
- 動的フィルター生成システム実装
- dialogs.jsonベースの設定管理

### 技術文書
- `DESIGN.md`: 設計原則
- `CLAUDE.md`: 開発記録
- `_FileOpenDlg_refact.md`: リファクタリング記録

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

プルリクエストやイシューの報告を歓迎します。