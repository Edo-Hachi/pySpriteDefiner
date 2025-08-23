# VSCode設定とUV環境対応ガイド

## 📋 **概要**
- **対象**: Python + UV仮想環境 + VSCodeデバッグ実行
- **作成日**: 2025-08-21
- **最終更新**: F5デバッグ実行問題解決後

---

## 🚨 **UV環境特有の注意点**

### **1. シンボリンク構造の理解**
UV環境では`.venv/bin/python3`がシンボリンクになります：
```bash
lrwxrwxrwx 1 user user   16 Aug 21 18:46 python -> /usr/bin/python3
lrwxrwxrwx 1 user user    6 Aug 21 18:46 python3 -> python
```

**影響**:
- VSCode Python拡張機能の認識問題
- デバッグアダプターの起動問題
- パス解決の複雑化

### **2. パス問題への対策**
**問題**: `ModuleNotFoundError: No module named 'config'`

**解決策**: main.py先頭でパス設定
```python
# VSCodeデバッグ用パス設定（UV環境対応）
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

### **3. 設定ファイルの複雑化回避**
**原因**: 試行錯誤による設定の蓄積
**結果**: VSCodeがsettings.jsonをPythonスクリプトとして実行する異常動作

**教訓**: **シンプルな設定から開始し、段階的に追加**

---

## ⚙️ **現在の動作確認済み設定**

### **launch.json**（デバッグ実行設定）
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: main.py",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "justMyCode": true
        }
    ]
}
```

**設定項目解説**:
- `"type": "debugpy"`: Python用デバッグアダプター
- `"program": "${workspaceFolder}/main.py"`: 実行対象ファイル
- `"console": "integratedTerminal"`: VSCode内蔵ターミナル使用
- `"cwd": "${workspaceFolder}"`: 作業ディレクトリ設定
- `"justMyCode": true`: ユーザーコードのみデバッグ対象

### **settings.json**（プロジェクト設定）
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python3"
}
```

**設定項目解説**:
- `"python.defaultInterpreterPath"`: デフォルトPythonインタープリター指定
- 相対パス使用でプロジェクト移動に対応

---

## 🛠️ **セットアップ手順**

### **1. 基本設定**
1. `.vscode/launch.json` 作成（上記内容）
2. `.vscode/settings.json` 作成（上記内容）
3. main.py先頭にパス設定コード追加

### **2. VSCode設定**
1. **Ctrl+Shift+P** → **"Python: Select Interpreter"**
2. `.venv/bin/python3`を選択（パス: `/path/to/project/.venv/bin/python3`）
3. 選択したインタープリターのバージョンが表示されることを確認

### **3. 動作確認**
1. **実行とデバッグ**パネル（Ctrl+Shift+D）を開く
2. **"Python: main.py"**が選択されていることを確認
3. **F5**でデバッグ実行
4. **Ctrl+F5**でデバッグなし実行も確認

---

## 🚫 **避けるべき設定パターン**

### **1. 過度に複雑なlaunch.json**
```json
// ❌ 避けるべき例
{
    "python": "${workspaceFolder}/.venv/bin/python3",
    "pythonArgs": ["-Xfrozen_modules=off"],
    "env": {
        "PYTHONPATH": "${workspaceFolder}:${env:PYTHONPATH}",
        "PYDEVD_DISABLE_FILE_VALIDATION": "1"
    },
    "envFile": "${workspaceFolder}/.env",
    "debugOptions": [
        "WaitOnAbnormalExit",
        "WaitOnNormalExit"
    ]
}
```

### **2. 不要な設定の蓄積**
```json
// ❌ 避けるべき例
{
  "python.terminal.activateEnvironment": true,
  "python.analysis.autoImportCompletions": true,
  "python.linting.enabled": false,
  "debug.allowBreakpointsEverywhere": true,
  "debug.console.acceptSuggestionOnEnter": "off",
  "python.analysis.extraPaths": ["${workspaceFolder}"],
  "python.autoComplete.extraPaths": ["${workspaceFolder}"]
}
```

---

## 🔧 **トラブルシューティング**

### **問題1: F5が反応しない**
**原因**: Python拡張機能がUV環境を認識していない

**解決策**:
1. VSCode完全再起動
2. Python: Select Interpreterで再選択
3. 設定ファイルをシンプル版に置き換え

### **問題2: ModuleNotFoundError**
**原因**: PYTHONPATH設定問題

**解決策**:
1. main.py先頭でsys.path.insert()追加
2. cwd設定確認
3. インタープリターパス確認

### **問題3: settings.jsonがPythonスクリプトとして実行される**
**原因**: launch.json設定の異常

**解決策**:
1. launch.jsonを削除して再作成
2. VSCodeワークスペースリロード
3. Python拡張機能の再インストール

---

## 📚 **参考コマンド**

### **環境確認**
```bash
# Python環境確認
.venv/bin/python3 --version
.venv/bin/python3 -c "import sys; print(sys.executable)"

# パッケージ確認
.venv/bin/python3 -c "import config; print('Config import: SUCCESS')"

# デバッグ用パス確認
.venv/bin/python3 -c "import sys; [print(f'  {p}') for p in sys.path]"
```

### **VSCode操作**
```
Ctrl+Shift+P : コマンドパレット
Ctrl+Shift+D : 実行とデバッグパネル
F5          : デバッグ実行
Ctrl+F5     : デバッグなし実行
```

---

## 🎯 **ベストプラクティス**

### **1. 設定管理**
- **シンプルから開始**: 最小構成で動作確認
- **段階的追加**: 必要に応じて設定追加
- **定期的見直し**: 不要設定の削除

### **2. 環境変更時の注意**
- **バックアップ**: 動作設定の保存
- **一つずつ変更**: 問題の切り分け
- **テスト確認**: 各段階での動作確認

### **3. トラブル対応**
- **ログ確認**: VSCodeの出力パネル確認
- **設定リセット**: 問題時はシンプル設定に戻す
- **完全再起動**: キャッシュクリアのため

---

## 📝 **更新履歴**
- **2025-08-21**: 初版作成（F5デバッグ問題解決後）
- UV環境でのVSCode設定問題と解決策を記録

---

*このドキュメントは実際の問題解決経験に基づいて作成されています*