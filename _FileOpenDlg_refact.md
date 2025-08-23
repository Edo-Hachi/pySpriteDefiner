# ファイルオープンダイアログ リファクタリング記録

## 概要
file_open_dialog.py における重複したフィルターマッピングコードのリファクタリング作業記録。
dialogs.json の定義情報を活用した動的フィルター生成システムの実装。

## 課題
ファイルフィルター定義が以下2箇所で重複していた：

### 1. file_open_dialog.py 内の重複コード
```python
# _apply_initial_filter() メソッド内
filter_mapping = {
    "All Files (*.*)": ["*.*"],
    "CSV Files (*.csv)": ["*.csv"], 
    "Text Files (*.txt)": ["*.txt"],
    "Python Files (*.py)": ["*.py"]
}

# handle_filter_changed() メソッド内
filter_mapping = {
    "All Files (*.*)": ["*.*"],
    "CSV Files (*.csv)": ["*.csv"],
    "Text Files (*.txt)": ["*.txt"], 
    "Python Files (*.py)": ["*.py"]
}
```

### 2. dialogs.json での定義
```json
{
  "type": "dropdown",
  "id": "IDC_FILE_FILTER",
  "items": ["Pyxel Resource (*.pyxres)", "All Files (*.*)", "CSV Files (*.csv)", "Text Files (*.txt)", "Python Files (*.py)"],
  "selected_index": 0
}
```

## 解決策

### 1. 動的フィルターマッピング生成メソッドの追加

```python
def _create_filter_mapping_from_widget(self):
    """ドロップダウンウィジェットから拡張子マッピングを動的に作成"""
    filter_widget = self._find_widget("IDC_FILE_FILTER")
    if not filter_widget or not hasattr(filter_widget, 'items'):
        return {}
        
    mapping = {}
    for item in filter_widget.items:
        # 拡張子を正規表現で抽出 (例: "Pyxel Resource (*.pyxres)" -> ["*.pyxres"])
        match = re.search(r'\((.*?)\)', item)
        if match:
            extensions_text = match.group(1)
            # カンマ区切りの拡張子に対応 (例: "*.txt,*.log" -> ["*.txt", "*.log"])
            extensions = [ext.strip() for ext in extensions_text.split(',')]
            mapping[item] = extensions
        else:
            # パターンが見つからない場合は全ファイル扱い
            mapping[item] = ["*.*"]
    
    return mapping
```

### 2. 重複コードの削除と統合

#### 修正前：
```python
def _apply_initial_filter(self):
    """ダイアログ初期化時にデフォルトフィルターを適用"""
    filter_widget = self._find_widget("IDC_FILE_FILTER")
    if filter_widget and hasattr(filter_widget, 'get_selected_value'):
        selected_filter = filter_widget.get_selected_value()
        if selected_filter:
            # ハードコードされたフィルターマッピング
            filter_mapping = {
                "All Files (*.*)": ["*.*"],
                "CSV Files (*.csv)": ["*.csv"],
                "Text Files (*.txt)": ["*.txt"],
                "Python Files (*.py)": ["*.py"]
            }
            
            filters = filter_mapping.get(selected_filter, ["*.*"])
            self.file_manager.set_file_filter(filters)
```

#### 修正後：
```python
def _apply_initial_filter(self):
    """ダイアログ初期化時にデフォルトフィルターを適用"""
    filter_widget = self._find_widget("IDC_FILE_FILTER")
    if filter_widget and hasattr(filter_widget, 'get_selected_value'):
        selected_filter = filter_widget.get_selected_value()
        if selected_filter:
            filter_mapping = self._create_filter_mapping_from_widget()
            filters = filter_mapping.get(selected_filter, ["*.*"])
            self.file_manager.set_file_filter(filters)
```

### 3. フィルター変更処理の簡素化

#### 修正前：
```python
def handle_filter_changed(self, selected_index: int, selected_value: str):
    """フィルタードロップダウンの選択が変更された時の処理"""
    # デバッグコメント多数
    
    # 選択されたフィルターに応じてファイルマネージャーのフィルターを設定
    filter_mapping = {
        "All Files (*.*)": ["*.*"],
        "CSV Files (*.csv)": ["*.csv"],
        "Text Files (*.txt)": ["*.txt"],
        "Python Files (*.py)": ["*.py"]
    }
    
    filters = filter_mapping.get(selected_value, ["*.*"])
    # デバッグコメント
    self.file_manager.set_file_filter(filters)
    
    # ファイルリストを更新
    # デバッグコメント
    self._refresh_file_list()
    self._setup_event_handlers()  # イベントハンドラーを再設定
    # デバッグコメント
```

#### 修正後：
```python
def handle_filter_changed(self, selected_index: int, selected_value: str):
    """フィルタードロップダウンの選択が変更された時の処理"""
    filter_mapping = self._create_filter_mapping_from_widget()
    filters = filter_mapping.get(selected_value, ["*.*"])
    self.file_manager.set_file_filter(filters)
    
    self._refresh_file_list()
    self._setup_event_handlers()
```

### 4. 必要なimportの追加

```python
import re  # 正規表現処理用
```

## 実装の特徴

### 1. 正規表現による拡張子抽出
- パターン: `r'\((.*?)\)'`
- 例: `"Pyxel Resource (*.pyxres)"` → `["*.pyxres"]`

### 2. 複数拡張子サポート
- カンマ区切り対応: `"Text Files (*.txt,*.log)"` → `["*.txt", "*.log"]`

### 3. フォールバック機能
- パターンマッチ失敗時は `["*.*"]` を設定

### 4. dialogs.json との完全連携
- JSONファイルでフィルター定義を変更するだけで自動反映
- コードの修正不要

## メリット

1. **DRY原則の遵守**: 重複コードの完全削除
2. **保守性向上**: フィルター定義の一元管理
3. **拡張性**: 新しいフィルターをJSONに追加するだけで対応
4. **可読性**: コードの簡素化とコメント削除
5. **柔軟性**: 複数拡張子やカスタムフィルターに対応

## 影響範囲

### 修正ファイル
- `file_open_dialog.py`: コアロジック修正

### 変更なしファイル  
- `dialogs.json`: 定義済みの構造を活用
- `file_utils.py`: フィルター処理は変更なし
- `widgets.py`: ドロップダウンウィジェット機能は変更なし

## 使用例

### dialogs.json でのフィルター拡張
```json
{
  "type": "dropdown",
  "id": "IDC_FILE_FILTER", 
  "items": [
    "Pyxel Resource (*.pyxres)",
    "All Files (*.*)",
    "Image Files (*.png,*.jpg,*.gif)",
    "Data Files (*.json,*.xml,*.yaml)"
  ],
  "selected_index": 0
}
```

上記のように定義すれば、自動的に以下のマッピングが生成される：
- `"Image Files (*.png,*.jpg,*.gif)"` → `["*.png", "*.jpg", "*.gif"]`
- `"Data Files (*.json,*.xml,*.yaml)"` → `["*.json", "*.xml", "*.yaml"]`

## 今後の展開

1. **他のダイアログへの適用**: save_dialog等にも同様のパターンを適用
2. **設定の外部化**: デフォルト選択インデックスもJSONで制御
3. **バリデーション追加**: 不正な拡張子パターンのチェック
4. **i18n対応**: 多言語フィルター名への対応

---
*作成日: 2025-08-23*
*対象プロジェクト: SpriteDefiner/DialogManager*