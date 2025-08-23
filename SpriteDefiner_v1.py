#!/usr/bin/env python3
"""
SpriteDefiner  - Enhanced Visual Sprite Definition Tool for Pyxel
"""

#ソースコードの中のコメントは日本語、英語を併記してください
##例
# :jp この関数はスプライトを表示します
# :en This function displays the sprite
# #画面に出力する文字列は英語にしてください。pyxelは日本語フォントを表示できません


import pyxel
import json
from collections import namedtuple
from enum import Enum

# アプリケーションの状態管理
class AppState(Enum):
    VIEW = "view"
    EDIT = "edit"
    COMMAND_INPUT = "command_input"
    LEGACY_INPUT = "legacy_input"
    SAVE_CONFIRM = "save_confirm"
    QUIT_CONFIRM = "quit_confirm"

# スプライト定義・編集用のPyxelビジュアルツール本体クラス
class SpriteDefiner:
    def __init__(self):
        # ウィンドウ設定
        self.WIDTH = 450  # 256 (sprite area) + 12*2 (margins) + 320 (right panel) = 620
        self.HEIGHT = 400  # ステータスエリア用に高さを増加
        
        # リソース設定
        self.RESOURCE_FILE = "./my_resource.pyxres"
        self.SPRITE_SIZE = 8
        
        # スプライトフィールド定義 - キーワードベース管理
        self.SPRITE_FIELDS = {
            'NAME': 'NAME',
            'ACT_NAME': 'ACT_NAME', 
            'FRAME_NUM': 'FRAME_NUM',
            'ANIM_SPD': 'ANIM_SPD',
            'LIFE': 'LIFE',
            'SCORE': 'SCORE', 
            'EXT3': 'EXT3',
            'EXT4': 'EXT4',
            'EXT5': 'EXT5'
        }
        
        # UI設定
        self.GRID_COLOR_VIEW = pyxel.COLOR_WHITE
        self.GRID_COLOR_EDIT = pyxel.COLOR_RED
        self.SELECT_COLOR = pyxel.COLOR_RED
        self.CURSOR_COLOR_VIEW = pyxel.COLOR_GREEN
        self.CURSOR_COLOR_EDIT = pyxel.COLOR_RED
        self.HOVER_COLOR = pyxel.COLOR_CYAN
        self.SPRITE_AREA_WIDTH = 256  # Full 256x256 sprite sheet
        self.SPRITE_AREA_HEIGHT = 256
        
        # 状態管理 - 新フォーマット: キーワードフィールド
        self.sprites = {}  # {key: {'x': x, 'y': y, 'NAME': name, 'ACT_NAME': val, 'FRAME_NUM': val, ...}}
        self.selected_sprite = None  # (x, y)
        self.cursor_sprite = (0, 0)  # 現在のカーソル位置 (x, y)
        self.hover_sprite = None  # マウスホバー位置 (x, y)
        
        # 編集履歴 - シンプルなスプライト名リスト
        self.edited_sprite_names = []  # 最近編集されたスプライト名のリスト
        
        # アプリケーション状態管理
        self.app_state = AppState.VIEW  # 現在の状態
        
        # 入力モード - キーワードフィールド対応
        self.input_text = ""  # レガシーテキスト入力
        self.command_mode = None  # 現在のコマンド: None, 'NAME', 'ACT_NAME', 'FRAME_NUM', 'ANIM_SPD', 'EXT1'-'EXT5'
        self.command_input = ""  # 現在のコマンド用入力テキスト
        self.edit_locked_sprite = None  # 編集中にロックされたスプライト位置
        
        
        self.message = "Use arrow keys to move (auto-select), F1 for EDIT, F2 for VIEW, Shift+Enter for legacy naming"
        
        # UI位置
        self.sprite_display_x = 12
        self.sprite_display_y = 12
        
        # カーソルと選択を同じ位置に初期化
        self.selected_sprite = self.cursor_sprite  # 初期位置を自動選択
        
        # Pyxelを初期化
        pyxel.init(self.WIDTH, self.HEIGHT, title="SpriteDefiner", quit_key=pyxel.KEY_NONE, display_scale=2)
        pyxel.load(self.RESOURCE_FILE)
        
        # 既存のsprites.jsonがあれば自動読み込み
        self._auto_load_sprites()
        
        pyxel.run(self.update, self.draw)
    
    # 起動時の自動読み込み処理
    def _auto_load_sprites(self):
        """起動時にsprites.jsonが存在すれば自動読み込み"""
        try:
            with open("sprites.json", "r", encoding="utf-8") as f:
                sprite_data = json.load(f)
            
            # 既存のスプライトをクリア
            self.sprites = {}
            
            # JSONからスプライトを読み込み（新フォーマット: キーワードフィールド）
            if "sprites" in sprite_data:
                for key, data in sprite_data["sprites"].items():
                    sprite_entry = {
                        'x': data['x'],
                        'y': data['y'], 
                        'NAME': data.get('NAME', 'NONAME')
                    }
                    
                    # キーワードフィールドをコピー
                    for field_key in self.SPRITE_FIELDS.values():
                        if field_key != 'NAME' and field_key in data:
                            sprite_entry[field_key] = data[field_key]
                    
                    self.sprites[key] = sprite_entry
            
            # 起動メッセージ
            self.message = f"Startup: Auto-loaded {len(self.sprites)} sprites from sprites.json"
        except FileNotFoundError:
            # JSONファイルが見つからない場合 - 通常起動
            self.message = "Startup: sprites.json not found - starting with empty sprite list"
        except json.JSONDecodeError:
            # 無効なJSON形式
            self.message = "Startup: Invalid sprites.json format - starting with empty sprite list"
        except Exception as e:
            # その他のエラー
            self.message = f"Startup: sprites.json load error - {e}"
    
    # メインループで呼ばれる更新処理。各種モードの入力受付や状態遷移を管理
    def update(self):
        """ゲームロジックの更新"""
        # 状態に応じた処理の振り分け
        if self.app_state == AppState.SAVE_CONFIRM:
            self._handle_save_confirmation()
        elif self.app_state == AppState.QUIT_CONFIRM:
            self._handle_quit_confirmation()
        elif self.app_state == AppState.LEGACY_INPUT:
            self._handle_text_input()
        elif self.app_state == AppState.COMMAND_INPUT:
            self._handle_command_input()
        elif self.app_state in [AppState.VIEW, AppState.EDIT]:
            self._handle_normal_input()
        
        # 保存機能 (F10 - VIEWモードのみ) - 確認付き
        if pyxel.btnp(pyxel.KEY_F10) and self.app_state == AppState.VIEW:
            self.app_state = AppState.SAVE_CONFIRM
            self.message = "Save to sprites.json? Y to confirm, N to cancel"
        
        # 読み込み機能 (F11 - VIEWモードのみ)
        if pyxel.btnp(pyxel.KEY_F11) and self.app_state == AppState.VIEW:
            self._load_from_json()
        
        # 終了 (F12のみ - VIEWモードのみ) - 確認付き
        if pyxel.btnp(pyxel.KEY_F12) and self.app_state == AppState.VIEW:
            self.app_state = AppState.QUIT_CONFIRM
            self.message = "Really quit? Y to confirm, N to cancel"
        
        # 安全のためESC/Q終了を無効化
        if pyxel.btnp(pyxel.KEY_Q) or pyxel.btnp(pyxel.KEY_ESCAPE):
            if self.app_state == AppState.EDIT:
                self.message = "Cannot quit in EDIT mode - Exit EDIT with F2 first"
            else:
                self.message = "Use F12 to quit (ESC/Q disabled for safety)"
    
    # キーボードカーソル移動処理
    def _handle_cursor_movement(self):
        """キーボードカーソル移動処理（VIEWモードのみ）"""
        if self.app_state != AppState.VIEW:
            return
            
        old_cursor = self.cursor_sprite
        
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.cursor_sprite = (max(0, self.cursor_sprite[0] - self.SPRITE_SIZE), self.cursor_sprite[1])
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.cursor_sprite = (min(self.SPRITE_AREA_WIDTH - self.SPRITE_SIZE, self.cursor_sprite[0] + self.SPRITE_SIZE), self.cursor_sprite[1])
        if pyxel.btnp(pyxel.KEY_UP):
            self.cursor_sprite = (self.cursor_sprite[0], max(0, self.cursor_sprite[1] - self.SPRITE_SIZE))
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.cursor_sprite = (self.cursor_sprite[0], min(self.SPRITE_AREA_HEIGHT - self.SPRITE_SIZE, self.cursor_sprite[1] + self.SPRITE_SIZE))
        
        # カーソル移動時に自動選択
        if old_cursor != self.cursor_sprite:
            self.selected_sprite = self.cursor_sprite
            self.message = f"Auto-selected sprite at {self.cursor_sprite}"

    # マウスホバー位置の更新処理
    def _update_hover_position(self):
        """マウスホバー位置の更新"""
        mouse_x = pyxel.mouse_x
        mouse_y = pyxel.mouse_y
        if (self.sprite_display_x <= mouse_x < self.sprite_display_x + self.SPRITE_AREA_WIDTH and
            self.sprite_display_y <= mouse_y < self.sprite_display_y + self.SPRITE_AREA_HEIGHT):
            rel_x = mouse_x - self.sprite_display_x
            rel_y = mouse_y - self.sprite_display_y
            hover_x = (rel_x // self.SPRITE_SIZE) * self.SPRITE_SIZE
            hover_y = (rel_y // self.SPRITE_SIZE) * self.SPRITE_SIZE
            self.hover_sprite = (hover_x, hover_y)
        else:
            self.hover_sprite = None

    # マウス・キーボード選択処理
    def _handle_selection_input(self):
        """マウス・キーボード選択処理"""
        # マウスクリック処理（EDITモードでは無効）
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and self.hover_sprite and self.app_state == AppState.VIEW:
            self.selected_sprite = self.hover_sprite
            self.cursor_sprite = self.hover_sprite
            self.message = f"Selected sprite at {self.hover_sprite}"
        
        # SPACEキーでの手動選択（自動選択が有効なので任意）
        if pyxel.btnp(pyxel.KEY_SPACE) and self.app_state == AppState.VIEW:
            self.selected_sprite = self.cursor_sprite
            self.message = f"Manually selected sprite at {self.cursor_sprite}"

    # モード切替処理
    def _handle_mode_switching(self):
        """モード切替処理（F1/F2）"""
        # F1でEDITモードに入る
        if pyxel.btnp(pyxel.KEY_F1) and self.app_state == AppState.VIEW:
            self.app_state = AppState.EDIT
            self.edit_locked_sprite = self.cursor_sprite
            self.message = f"EDIT mode: Sprite ({self.cursor_sprite[0]}, {self.cursor_sprite[1]}) locked - Commands: N, 1, 2, 3"
        
        # F2でEDITモードを終了（コマンド入力モードでない場合のみ）
        if pyxel.btnp(pyxel.KEY_F2) and self.app_state == AppState.EDIT and not self.command_mode:
            # EDITモード終了時に自動保存
            self._save_to_json()
            self.app_state = AppState.VIEW
            self.edit_locked_sprite = None
            self.message = "VIEW mode - Changes auto-saved"

    # EDITモード時のコマンド処理
    def _handle_edit_commands(self):
        """EDITモード時のコマンド処理"""
        if self.app_state != AppState.EDIT:
            return
            
        # F3でEDITモード中の手動保存
        if pyxel.btnp(pyxel.KEY_F3):
            self._save_to_json()
        
        if pyxel.btnp(pyxel.KEY_N):
            self.command_mode = 'NAME'
            self.command_input = ""
            self.app_state = AppState.COMMAND_INPUT
            self.message = "Enter sprite name:"
        elif pyxel.btnp(pyxel.KEY_1):
            self.command_mode = 'ACT_NAME'
            self.command_input = ""
            self.app_state = AppState.COMMAND_INPUT
            self.message = "Enter ACT_NAME:"
        elif pyxel.btnp(pyxel.KEY_2):
            self.command_mode = 'FRAME_NUM'
            self.command_input = ""
            self.app_state = AppState.COMMAND_INPUT
            self.message = "Enter FRAME_NUM:"
        elif pyxel.btnp(pyxel.KEY_3):
            self.command_mode = 'ANIM_SPD'
            self.command_input = ""
            self.app_state = AppState.COMMAND_INPUT
            self.message = "Enter ANIM_SPD:"
        # 拡張フィールド（4-8キー）
        elif pyxel.btnp(pyxel.KEY_4):
            self.command_mode = 'EXT1'
            self.command_input = ""
            self.app_state = AppState.COMMAND_INPUT
            self.message = "Enter EXT1:"
        elif pyxel.btnp(pyxel.KEY_5):
            self.command_mode = 'EXT2'
            self.command_input = ""
            self.app_state = AppState.COMMAND_INPUT
            self.message = "Enter EXT2:"
        elif pyxel.btnp(pyxel.KEY_6):
            self.command_mode = 'EXT3'
            self.command_input = ""
            self.app_state = AppState.COMMAND_INPUT
            self.message = "Enter EXT3:"
        elif pyxel.btnp(pyxel.KEY_7):
            self.command_mode = 'EXT4'
            self.command_input = ""
            self.app_state = AppState.COMMAND_INPUT
            self.message = "Enter EXT4:"
        elif pyxel.btnp(pyxel.KEY_8):
            self.command_mode = 'EXT5'
            self.command_input = ""
            self.app_state = AppState.COMMAND_INPUT
            self.message = "Enter EXT5:"

    # レガシー入力モードの処理
    def _handle_legacy_input_trigger(self):
        """レガシー命名モードのトリガー処理（意図的使用のためShift+Enter）"""
        if (pyxel.btnp(pyxel.KEY_RETURN) and pyxel.btn(pyxel.KEY_SHIFT) and 
            self.selected_sprite and self.app_state == AppState.VIEW):
            self.app_state = AppState.LEGACY_INPUT
            self.input_text = ""
            self.message = "Enter sprite name (legacy mode):"

    # VIEWモード時の通常操作（カーソル移動・選択・モード切替など）を処理
    def _handle_normal_input(self):
        """通常入力処理（カーソル移動、モード切替）"""
        self._handle_cursor_movement()
        self._update_hover_position()
        self._handle_selection_input()
        self._handle_mode_switching()
        
        # EDITモードでのみ編集コマンドを処理
        if self.app_state == AppState.EDIT:
            self._handle_edit_commands()
        
        # VIEWモードでのみレガシー入力トリガーを処理
        if self.app_state == AppState.VIEW:
            self._handle_legacy_input_trigger()
    
    # 共通の文字入力処理
    def _handle_text_input_common(self, input_text):
        """共通テキスト入力処理 - 更新されたテキストを返す"""
        # 文字入力処理
        for i in range(26):  # A-Z
            if pyxel.btnp(pyxel.KEY_A + i):
                if pyxel.btn(pyxel.KEY_SHIFT):
                    input_text += chr(ord('A') + i)
                else:
                    input_text += chr(ord('a') + i)
        
        # 数字
        for i in range(10):
            if pyxel.btnp(pyxel.KEY_0 + i):
                input_text += str(i)
        
        # アンダースコア
        if pyxel.btnp(pyxel.KEY_MINUS) and pyxel.btn(pyxel.KEY_SHIFT):
            input_text += "_"
        
        # バックスペース
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            if input_text:
                input_text = input_text[:-1]
        
        return input_text

    # コマンド入力モード時のキー入力処理（名前やタグの編集）
    def _handle_command_input(self):
        """コマンド入力モード処理"""
        # 共通テキスト入力処理を使用
        self.command_input = self._handle_text_input_common(self.command_input)
        
        # 入力確定
        if pyxel.btnp(pyxel.KEY_RETURN):
            self._process_command()
        
        # 入力キャンセル
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.command_mode = None
            self.command_input = ""
            self.app_state = AppState.EDIT
            self.message = "Command cancelled"
    
    # 旧式の名前入力モードのキー入力処理
    def _handle_text_input(self):
        """レガシーテキスト入力処理（スプライト命名用）"""
        # 共通テキスト入力処理を使用
        self.input_text = self._handle_text_input_common(self.input_text)
        
        # 入力確定
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.input_text and self.selected_sprite:
                sprite_key = f"{self.selected_sprite[0]}_{self.selected_sprite[1]}"
                self.sprites[sprite_key] = {
                    'x': self.selected_sprite[0],
                    'y': self.selected_sprite[1],
                    'NAME': self.input_text,
                    'ACT_NAME': 'UNDEF'  # 新フォーマット: デフォルト値
                }
                self.message = f"Added sprite '{self.input_text}'"
                self.selected_sprite = None
            self.app_state = AppState.VIEW
            self.input_text = ""
        
        # 入力キャンセル
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.app_state = AppState.VIEW
            self.input_text = ""
            self.message = "Cancelled"
    
    # 共通のY/N確認入力処理
    def _handle_confirmation_input(self, on_yes, on_no, cancel_message):
        """共通のY/N確認入力処理"""
        if pyxel.btnp(pyxel.KEY_Y):
            on_yes()
        elif pyxel.btnp(pyxel.KEY_N) or pyxel.btnp(pyxel.KEY_ESCAPE):
            on_no()
            self.message = cancel_message

    # F10保存時のY/N確認入力を処理
    def _handle_save_confirmation(self):
        """保存用Y/N確認処理"""
        def on_yes():
            self.app_state = AppState.VIEW
            self._save_to_json()
        
        def on_no():
            self.app_state = AppState.VIEW
        
        self._handle_confirmation_input(on_yes, on_no, "Save cancelled")
    
    # F12終了時のY/N確認入力を処理
    def _handle_quit_confirmation(self):
        """終了用Y/N確認処理"""
        def on_yes():
            pyxel.quit()
        
        def on_no():
            self.app_state = AppState.VIEW
        
        self._handle_confirmation_input(on_yes, on_no, "Quit cancelled")
    
    # 指定位置のスプライトを検索
    def _find_sprite_at_position(self, x, y):
        """指定位置のスプライトを検索"""
        for key, data in self.sprites.items():
            if data['x'] == x and data['y'] == y:
                return key
        return None

    # スプライト名設定の処理
    def _process_name_command(self, x, y):
        """NAME コマンドの処理"""
        if not self.command_input:
            return
            
        # この位置の既存スプライトを検索して既存フィールドを保持
        existing_fields = {}
        sprite_key = f"{x}_{y}"  # 位置を一意キーとして使用
        
        for key, data in list(self.sprites.items()):
            if data['x'] == x and data['y'] == y:
                # 既存のキーワードフィールドを保持
                for field_key in self.SPRITE_FIELDS.values():
                    if field_key != 'name' and field_key in data:
                        existing_fields[field_key] = data[field_key]
                del self.sprites[key]
                break
        
        # 新しいスプライトエントリを作成
        sprite_entry = {
            'x': x,
            'y': y,
            'NAME': self.command_input  # グループ名（複数スプライトで同じ名前が可能）
        }
        
        # 既存フィールドをコピー
        sprite_entry.update(existing_fields)
        
        self.sprites[sprite_key] = sprite_entry
        
        # 編集済みスプライト名リストに追加
        self._add_edited_sprite_name(self.command_input)
        self.message = f"Set group name '{self.command_input}' to sprite ({x}, {y})"

    # フィールド設定の処理
    def _process_field_command(self, x, y):
        """ACT_NAME/FRAME_NUM/ANIM_SPD/EXT フィールドコマンドの処理"""
        sprite_key = self._find_sprite_at_position(x, y)
        
        if sprite_key:
            if self.command_input:
                # 新フォーマット: 直接フィールドに設定
                field_key = self.command_mode  # 'ACT_NAME', 'FRAME_NUM', 'ANIM_SPD', 'EXT1'-'EXT5'
                
                if field_key in self.SPRITE_FIELDS.values():
                    self.sprites[sprite_key][field_key] = self.command_input
                    
                    # 編集済みスプライト名リストに追加（現在のスプライト名を取得）
                    sprite_name = self.sprites[sprite_key].get('NAME', 'NONAME')
                    self._add_edited_sprite_name(sprite_name)
                    self.message = f"Set {self.command_mode} to '{self.command_input}'"
                else:
                    self.message = f"Unknown field: {self.command_mode}"
            else:
                self.message = "Cannot set empty field"
        else:
            # この位置にスプライトがない場合は新規作成
            sprite_key = f"{x}_{y}"
            self.sprites[sprite_key] = {
                'x': x,
                'y': y,
                'NAME': 'NONAME',
                'ACT_NAME': 'UNDEF'  # 新フォーマット: デフォルト値
            }
            self.message = "Created new sprite - Set NAME first"

    # コマンド入力完了時の処理（スプライト名やフィールドの設定）
    def _process_command(self):
        """完了したコマンドの処理"""
        # EDITモードではロックされたスプライト位置を使用
        x, y = self.edit_locked_sprite if self.edit_locked_sprite else self.cursor_sprite
        
        if self.command_mode == 'NAME':
            self._process_name_command(x, y)
        elif self.command_mode in ['ACT_NAME', 'FRAME_NUM', 'ANIM_SPD', 'EXT1', 'EXT2', 'EXT3', 'EXT4', 'EXT5']:
            self._process_field_command(x, y)
        
        # コマンドモードをリセット
        self.command_mode = None
        self.command_input = ""
        self.app_state = AppState.EDIT
    
    # 最近編集したスプライト名リストを管理（重複排除・最大6件）
    def _add_edited_sprite_name(self, sprite_name):
        """最近編集されたリストにスプライト名を追加"""
        # 重複を避けるため既存があれば削除
        if sprite_name in self.edited_sprite_names:
            self.edited_sprite_names.remove(sprite_name)
        
        # 末尾に追加
        self.edited_sprite_names.append(sprite_name)
        
        # 最新6件のみを保持
        if len(self.edited_sprite_names) > 6:
            self.edited_sprite_names = self.edited_sprite_names[-6:]
    
    # スプライト情報をJSONファイルに保存
    def _save_to_json(self):
        """スプライトをJSONファイルに保存"""
        sprite_data = {
            "meta": {
                "sprite_size": self.SPRITE_SIZE,
                "resource_file": self.RESOURCE_FILE,
                "created_by": "SpriteDefiner",
                "version": "3.0"
            },
            "sprites": {}
        }
        
        for key, data in self.sprites.items():
            sprite_entry = {
                "x": data['x'], 
                "y": data['y'],
                "NAME": data.get('NAME', 'NONAME')
            }
            
            # キーワードフィールドを追加
            for field_key in self.SPRITE_FIELDS.values():
                if field_key != 'name' and field_key in data:
                    sprite_entry[field_key] = data[field_key]
            
            sprite_data["sprites"][key] = sprite_entry
        
        try:
            with open("sprites.json", "w", encoding="utf-8") as f:
                json.dump(sprite_data, f, indent=2, ensure_ascii=False)
            
            # 状況に応じて異なるメッセージを表示
            if self.app_state == AppState.EDIT:
                self.message = f"Saved {len(self.sprites)} sprites (EDIT mode active)"
            else:
                self.message = f"F10: Saved {len(self.sprites)} sprites to sprites.json"
        except Exception as e:
            # 保存失敗時のエラーメッセージ
            self.message = f"Save error: {e}"
    
    def _load_from_json(self):
        """JSONファイルからスプライトを読み込み"""
        try:
            with open("sprites.json", "r", encoding="utf-8") as f:
                sprite_data = json.load(f)
            
            # 既存のスプライト情報をクリア
            self.sprites = {}
            
            # JSONからスプライト情報を読み込む（新フォーマット対応）
            if "sprites" in sprite_data:
                for key, data in sprite_data["sprites"].items():
                    sprite_entry = {
                        'x': data['x'],
                        'y': data['y'], 
                        'NAME': data.get('NAME', 'NONAME')
                    }
                    
                    # キーワードフィールドをコピー
                    for field_key in self.SPRITE_FIELDS.values():
                        if field_key != 'NAME' and field_key in data:
                            sprite_entry[field_key] = data[field_key]
                    
                    self.sprites[key] = sprite_entry
                    
            self.message = f"F11: Loaded {len(self.sprites)} sprites from sprites.json"
        except FileNotFoundError:
            # JSONファイルが存在しない場合のメッセージ
            self.message = "F11: sprites.json file not found"
        except Exception as e:
            # 読み込み失敗時のエラーメッセージ
            self.message = f"Load error: {e}"
    
    def draw(self):
        """アプリケーション全体の描画処理"""
        pyxel.cls(pyxel.COLOR_BLACK)
        
        # スプライトシートの描画
        self._draw_sprite_sheet()
        
        # グリッドの描画
        self._draw_grid()
        
        # マウスホバー時のハイライト描画
        self._draw_hover()
        
        # カーソル描画
        self._draw_cursor()
        
        # 選択ハイライト描画
        self._draw_selection()
        
        # マウスカーソル描画
        self._draw_mouse_cursor()
        
        # グリッド下のステータスエリア描画
        status_y = self.sprite_display_y + self.SPRITE_AREA_HEIGHT + 10
        self._draw_status_area(status_y)
        
        # 右パネル描画
        sprite_list_x = self.sprite_display_x + self.SPRITE_AREA_WIDTH + 20
        self._draw_dynamic_info(sprite_list_x)
        
        # 最近編集されたスプライト名描画（右端に常時表示）
        recent_names_x = sprite_list_x + 120  # 右端に配置（wider sprite area requires more space）
        self._draw_recent_sprite_names(recent_names_x)
        
        # コントロール（下部）
        controls_y = self.HEIGHT - 25
        if self.app_state == AppState.EDIT:
            pyxel.text(10, controls_y, "EDIT mode active - movement locked | F2: Exit+Save | F3: Save", pyxel.COLOR_RED)
        else:
            pyxel.text(10, controls_y, "Arrow Keys: Auto-Select | F1: EDIT | F10: Save | F11: Load | F12: Quit | Shift+Enter: Legacy", pyxel.COLOR_PINK)
        pyxel.text(10, controls_y + 8, f"Cursor: ({self.cursor_sprite[0]}, {self.cursor_sprite[1]})", pyxel.COLOR_GRAY)
    
    def _draw_sprite_sheet(self):
        """イメージバンク0からスプライトシートを描画"""
        pyxel.blt(self.sprite_display_x, self.sprite_display_y, 
                 0, 0, 0, 
                 self.SPRITE_AREA_WIDTH, self.SPRITE_AREA_HEIGHT)
    
    def _draw_grid(self):
        """スプライトシート上にグリッド線を描画"""
        # モードに基づいてグリッド色を選択（EDITとCOMMAND_INPUTの両方でEDIT色を使用）
        grid_color = self.GRID_COLOR_EDIT if self.app_state in [AppState.EDIT, AppState.COMMAND_INPUT] else self.GRID_COLOR_VIEW
        
        # 垂直線
        for x in range(0, self.SPRITE_AREA_WIDTH + 1, self.SPRITE_SIZE):
            line_x = self.sprite_display_x + x
            pyxel.line(
                line_x, self.sprite_display_y,
                line_x, self.sprite_display_y + self.SPRITE_AREA_HEIGHT,
                grid_color
            )
        
        # 水平線
        for y in range(0, self.SPRITE_AREA_HEIGHT + 1, self.SPRITE_SIZE):
            line_y = self.sprite_display_y + y
            pyxel.line(
                self.sprite_display_x, line_y,
                self.sprite_display_x + self.SPRITE_AREA_WIDTH, line_y,
                grid_color
            )
    
    def _draw_hover(self):
        """ホバーハイライトを描画"""
        if self.hover_sprite:
            x, y = self.hover_sprite
            rect_x = self.sprite_display_x + x
            rect_y = self.sprite_display_y + y
            pyxel.rectb(rect_x, rect_y, self.SPRITE_SIZE, self.SPRITE_SIZE, self.HOVER_COLOR)
    
    def _draw_cursor(self):
        """キーボードカーソルを描画"""
        # モードに基づいてカーソル色を選択（EDITとCOMMAND_INPUTの両方でEDIT色を使用）
        cursor_color = self.CURSOR_COLOR_EDIT if self.app_state in [AppState.EDIT, AppState.COMMAND_INPUT] else self.CURSOR_COLOR_VIEW
        
        # EDITモードではロックされたスプライト位置を表示、VIEWモードでは現在のカーソルを表示
        if self.app_state == AppState.EDIT and self.edit_locked_sprite:
            x, y = self.edit_locked_sprite
            # ロックされたスプライト用に太いカーソルを描画
            rect_x = self.sprite_display_x + x
            rect_y = self.sprite_display_y + y
            pyxel.rectb(rect_x, rect_y, self.SPRITE_SIZE, self.SPRITE_SIZE, cursor_color)
            pyxel.rectb(rect_x + 1, rect_y + 1, self.SPRITE_SIZE - 2, self.SPRITE_SIZE - 2, cursor_color)
            pyxel.rectb(rect_x + 2, rect_y + 2, self.SPRITE_SIZE - 4, self.SPRITE_SIZE - 4, cursor_color)
        else:
            x, y = self.cursor_sprite
            rect_x = self.sprite_display_x + x
            rect_y = self.sprite_display_y + y
            pyxel.rectb(rect_x, rect_y, self.SPRITE_SIZE, self.SPRITE_SIZE, cursor_color)
            pyxel.rectb(rect_x + 1, rect_y + 1, self.SPRITE_SIZE - 2, self.SPRITE_SIZE - 2, cursor_color)
    
    def _draw_selection(self):
        """選択ハイライトを描画"""
        if self.selected_sprite:
            x, y = self.selected_sprite
            rect_x = self.sprite_display_x + x
            rect_y = self.sprite_display_y + y
            pyxel.rectb(rect_x, rect_y, self.SPRITE_SIZE, self.SPRITE_SIZE, self.SELECT_COLOR)
    
    def _draw_mouse_cursor(self):
        """カスタムマウスカーソルを描画"""
        mouse_x = pyxel.mouse_x
        mouse_y = pyxel.mouse_y
        pyxel.line(mouse_x - 3, mouse_y, mouse_x + 3, mouse_y, pyxel.COLOR_WHITE)
        pyxel.line(mouse_x, mouse_y - 3, mouse_x, mouse_y + 3, pyxel.COLOR_WHITE)
        pyxel.pset(mouse_x, mouse_y, pyxel.COLOR_RED)
    
    def _draw_status_area(self, y_pos):
        """グリッド下のステータスエリアを描画"""
        # 次のアクションを明確にしたモードインジケータ
        if self.app_state == AppState.EDIT:
            if self.edit_locked_sprite:
                lock_info = f" Locked ({self.edit_locked_sprite[0]}, {self.edit_locked_sprite[1]})"
                pyxel.text(10, y_pos, f"F2>VIEW [EDIT{lock_info}]", pyxel.COLOR_RED)
            else:
                pyxel.text(10, y_pos, "F2>VIEW [EDIT]", pyxel.COLOR_RED)
        else:
            pyxel.text(10, y_pos, "F1>EDIT [VIEW]", pyxel.COLOR_GREEN)
        
        # コマンドオプション（EDITモードのみ）
        if self.app_state == AppState.EDIT and not self.command_mode:
            pyxel.text(10, y_pos + 12, "Commands: [N:Name] [1-3:DIC] [4-8:EXT] [F3:Save]", pyxel.COLOR_CYAN)
        
        # コマンド入力プロンプト
        if self.app_state == AppState.COMMAND_INPUT:
            prompt_text = f"{self.command_mode}> {self.command_input}_"
            pyxel.text(10, y_pos + 24, prompt_text, pyxel.COLOR_YELLOW)
        
        # 保存確認プロンプト
        if self.app_state == AppState.SAVE_CONFIRM:
            pyxel.text(10, y_pos + 24, "Save to sprites.json? [Y]Yes / [N]No / [ESC]Cancel", pyxel.COLOR_YELLOW)
        
        # 終了確認プロンプト
        if self.app_state == AppState.QUIT_CONFIRM:
            pyxel.text(10, y_pos + 24, "Really quit? [Y]Yes / [N]No / [ESC]Cancel", pyxel.COLOR_RED)
        
        # メッセージ
        message_color = pyxel.COLOR_YELLOW if self.app_state in [AppState.SAVE_CONFIRM, AppState.QUIT_CONFIRM] else pyxel.COLOR_WHITE
        pyxel.text(10, y_pos + 36, self.message, message_color)
    
    # 現在の対象スプライト情報を取得
    def _get_current_sprite_info(self):
        """現在のスプライト情報を取得（位置、名前、タグ）"""
        # EDITモードではロックされたスプライト情報を表示、VIEWモードではカーソル情報を表示
        if self.app_state == AppState.EDIT and self.edit_locked_sprite:
            x, y = self.edit_locked_sprite
        else:
            x, y = self.cursor_sprite
        
        sprite_number = self._get_sprite_number(x, y)
        
        # カーソル位置でスプライトデータを検索（新フォーマット対応）
        sprite_name = "NONAME"
        sprite_data = {}
        
        for key, data in self.sprites.items():
            if data['x'] == x and data['y'] == y:
                sprite_name = data.get('NAME', 'NONAME')
                sprite_data = data
                break
        
        return x, y, sprite_number, sprite_name, sprite_data

    def _draw_dynamic_info(self, x_pos):
        """カーソル位置に基づく動的スプライト情報を描画"""
        x, y, sprite_number, sprite_name, sprite_data = self._get_current_sprite_info()
        
        # ヘッダー - 常時表示
        pyxel.text(x_pos, self.sprite_display_y, "Sprite Details", pyxel.COLOR_CYAN)
        pyxel.text(x_pos, self.sprite_display_y + 12, f"Position: ({x}, {y})", pyxel.COLOR_WHITE)
        pyxel.text(x_pos, self.sprite_display_y + 22, f"Number: #{sprite_number}", pyxel.COLOR_WHITE)
        pyxel.text(x_pos, self.sprite_display_y + 32, f"N]Name: {sprite_name}", pyxel.COLOR_YELLOW)
        
        # フィールド情報（新フォーマット）
        act_name = sprite_data.get('ACT_NAME', 'NO_ACT')
        frame_num = sprite_data.get('FRAME_NUM', 'NO_FRAME')
        anim_speed = sprite_data.get('ANIM_SPD', 'NO_SPEED')
        
        pyxel.text(x_pos, self.sprite_display_y + 42, f"1]ACT_NAME: {act_name}", pyxel.COLOR_GREEN)
        pyxel.text(x_pos, self.sprite_display_y + 52, f"2]FRAME_NUM: {frame_num}", pyxel.COLOR_GREEN)
        pyxel.text(x_pos, self.sprite_display_y + 62, f"3]ANIM_SPD: {anim_speed}", pyxel.COLOR_GREEN)
        
        # EXT情報
        ext1 = sprite_data.get('EXT1', 'NO_EXT')
        ext2 = sprite_data.get('EXT2', 'NO_EXT')
        ext3 = sprite_data.get('EXT3', 'NO_EXT')
        ext4 = sprite_data.get('EXT4', 'NO_EXT')
        ext5 = sprite_data.get('EXT5', 'NO_EXT')
        
        pyxel.text(x_pos, self.sprite_display_y + 72, f"4]EXT1: {ext1}", pyxel.COLOR_GRAY)
        pyxel.text(x_pos, self.sprite_display_y + 82, f"5]EXT2: {ext2}", pyxel.COLOR_GRAY)
        pyxel.text(x_pos, self.sprite_display_y + 92, f"6]EXT3: {ext3}", pyxel.COLOR_GRAY)
        pyxel.text(x_pos, self.sprite_display_y + 102, f"7]EXT4: {ext4}", pyxel.COLOR_GRAY)
        pyxel.text(x_pos, self.sprite_display_y + 112, f"8]EXT5: {ext5}", pyxel.COLOR_GRAY)
        
        # モードインジケータ
        mode_text = "EDIT" if self.app_state == AppState.EDIT else "VIEW"
        mode_color = pyxel.COLOR_RED if self.app_state == AppState.EDIT else pyxel.COLOR_GREEN
        pyxel.text(x_pos, self.sprite_display_y + 124, f"Mode: {mode_text}", mode_color)
        
        # モードに基づくコンテンツ
        if self.app_state == AppState.EDIT:
            self._draw_edit_content(x_pos, sprite_data)
        else:
            self._draw_view_content(x_pos)
    
    def _draw_edit_content(self, x_pos, sprite_data):
        """編集モードのコンテンツを描画"""
        start_y = self.sprite_display_y + 138  # DIC+EXT表示に対応するため下に移動
        
        pyxel.text(x_pos, start_y, "Current Fields:", pyxel.COLOR_WHITE)
        
        field_y = 12
        field_count = 0
        for field_key in ['ACT_NAME', 'FRAME_NUM', 'ANIM_SPD']:
            if field_key in sprite_data:
                field_name = f"{field_key}: {sprite_data[field_key]}"
                pyxel.text(x_pos, start_y + field_y, field_name, pyxel.COLOR_GREEN)
                field_y += 10
                field_count += 1
        
        if field_count == 0:
            pyxel.text(x_pos, start_y + field_y, "No fields defined", pyxel.COLOR_GRAY)
    
    def _draw_view_content(self, x_pos):
        """ビューモードのコンテンツを描画 - シンプルなステータス"""
        start_y = self.sprite_display_y + 138  # DIC+EXT表示に対応するため下に移動
        
        pyxel.text(x_pos, start_y, f"Total Sprites: {len(self.sprites)}", pyxel.COLOR_CYAN)
        pyxel.text(x_pos, start_y + 12, "F1 to edit mode", pyxel.COLOR_GRAY)
    
    def _draw_recent_sprite_names(self, x_pos):
        """右端に最近編集されたスプライト名を描画（常時表示）"""
        start_y = self.sprite_display_y
        
        # 編集モードインジケータ付きヘッダー
        if self.app_state == AppState.EDIT:
            pyxel.text(x_pos, start_y, "Recent Edit", pyxel.COLOR_RED)
        else:
            pyxel.text(x_pos, start_y, "Recent Edit", pyxel.COLOR_CYAN)
        
        pyxel.text(x_pos, start_y + 10, f"({len(self.edited_sprite_names)})", pyxel.COLOR_GRAY)
        
        if self.edited_sprite_names:
            # 最新6つのスプライト名を表示
            y_offset = 22
            for i, sprite_name in enumerate(self.edited_sprite_names[-6:]):
                # 最新を黄色でハイライト、他は白
                color = pyxel.COLOR_YELLOW if i == len(self.edited_sprite_names[-6:]) - 1 else pyxel.COLOR_WHITE
                
                # 長い名前は切り詰めて表示
                display_name = sprite_name[:8] + "..." if len(sprite_name) > 8 else sprite_name
                pyxel.text(x_pos, start_y + y_offset, display_name, color)
                y_offset += 10
        else:
            pyxel.text(x_pos, start_y + 22, "None yet", pyxel.COLOR_GRAY)
    
    def _get_sprite_number(self, x, y):
        """位置に基づいてスプライト番号を計算"""
        grid_x = x // self.SPRITE_SIZE
        grid_y = y // self.SPRITE_SIZE
        return grid_y * (self.SPRITE_AREA_WIDTH // self.SPRITE_SIZE) + grid_x


if __name__ == "__main__":
    SpriteDefiner()