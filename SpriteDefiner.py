#!/usr/bin/env python3
"""
SpriteDefiner - Enhanced Visual Sprite Definition Tool for Pyxel (Ver.2)
"""

# :jp ソースコードの中のコメントは日本語、英語を併記してください
# :en Comments in the source code should be written in both Japanese and English.
# :jp 画面に出力する文字列は英語にしてください。pyxelは日本語フォントを表示できません
# :en Please use English for the text displayed on the screen, as Pyxel cannot display Japanese fonts.

import pyxel
import os
import sys
import json
import shutil

# :jp SpriteDefinerDlgモジュールへのパスを追加
# :en Add the path to the SpriteDefinerDlg module
sys.path.append(os.path.join(os.path.dirname(__file__), 'SpriteDefinerDlg'))

from dialog_manager import DialogManager
from file_open_dialog import FileOpenDialogController
from sprite_edit_dialog import SpriteEditDialogController

class SpriteDefiner:
    def __init__(self):
        # :jp ウィンドウ設定
        # :en Window settings
        self.WIDTH = 256
        self.HEIGHT = 256

        # :jp Pyxelを初期化
        # :en Initialize Pyxel
        pyxel.init(self.WIDTH, self.HEIGHT, title="SpriteDefiner Ver.2", quit_key=pyxel.KEY_Q, display_scale=2)

        pyxel.load("my_resource.pyxres")  # 空のリソースファイルをロードしておく


        # :jp DialogManagerを初期化
        # :en Initialize DialogManager
        dialogs_json_path = os.path.join(os.path.dirname(__file__), 'SpriteDefinerDlg', 'dialogs.json')
        self.dialog_manager = DialogManager(dialogs_json_path)

        # :jp FileOpenDialogControllerを初期化
        # :en Initialize FileOpenDialogController
        self.file_open_controller = FileOpenDialogController(self.dialog_manager, ".")
        
        # :jp SpriteEditDialogControllerを初期化
        # :en Initialize SpriteEditDialogController
        self.sprite_edit_controller = SpriteEditDialogController(self.dialog_manager)

        # :jp 読み込まれたリソースファイル情報
        # :en Loaded resource file information
        self.loaded_pyxres_file = None
        self.resource_loaded = False

        # :jp スプライト表示設定
        # :en Sprite display settings
        self.display_x = 8
        self.display_y = 32
        self.scroll_x = 0
        self.scroll_y = 0
        
        # :jp タイル選択状態
        # :en Tile selection state
        self.selected_tile_x = None  # リソースファイル座標系でのX座標
        self.selected_tile_y = None  # リソースファイル座標系でのY座標
        
        # :jp スプライト定義データ
        # :en Sprite definition data
        self.sprite_data = None
        self.sprite_json_file = None

        # :jp コマンドパレットを初期化
        # :en Initialize the command palette
        self.init_command_palette()

        pyxel.mouse(True)

        # :jp アプリケーションを実行
        # :en Run the application
        pyxel.run(self.update, self.draw)

    def init_command_palette(self):
        """
        :jp コマンドパレットのボタンを定義します。
        :en Define the buttons for the command palette.
        """
        self.command_buttons = []
        button_defs = [
            {'label': 'LOAD(F1)', 'key': pyxel.KEY_F1, 'action': self.action_load},
            {'label': 'RESET(F2)', 'key': pyxel.KEY_F2, 'action': self.action_toggle_viewport_size},
            # {'label': 'SAVE(F3)', 'key': pyxel.KEY_F3, 'action': self.action_save}, # :jp 将来の実装用 # :en For future implementation
        ]
        
        x_offset = 5
        y_offset = 5
        button_width = 60
        button_height = 13
        button_spacing = 5

        for i, b_def in enumerate(button_defs):
            button = {
                'label': b_def['label'],
                'key': b_def['key'],
                'action': b_def['action'],
                'rect': (x_offset + i * (button_width + button_spacing), y_offset, button_width, button_height),
                'is_hover': False
            }
            self.command_buttons.append(button)

    def action_load(self):
        """
        :jp LOADアクション（ファイルオープンダイアログ表示）
        :en LOAD action (shows the file open dialog)
        """
        self.file_open_controller.show_file_open_dialog()
    
    def action_toggle_viewport_size(self):
        """
        :jp SIZEアクション（スクロール位置リセット）
        :en SIZE action (reset scroll position)
        """
        # スクロール位置をリセット
        self.scroll_x = 0
        self.scroll_y = 0

    def check_file_open_result(self):
        """
        :jp ファイルオープンダイアログの結果をチェックし、pyxresファイルを読み込みます
        :en Check file open dialog result and load pyxres file
        """
        if not self.file_open_controller.is_active():
            result = self.file_open_controller.get_result()
            if result and result.endswith('.pyxres'):
                self.load_pyxres_file(result)
                # :jp 結果をクリアして重複処理を防ぐ
                # :en Clear result to prevent duplicate processing
                self.file_open_controller.result = None

    def load_pyxres_file(self, file_path):
        """
        :jp pyxresファイルを読み込みます
        :en Load pyxres file
        """
        try:
            if os.path.exists(file_path):
                # :jp Pyxelにリソースファイルを読み込み
                # :en Load resource file into Pyxel
                pyxel.load(file_path)
                
                self.loaded_pyxres_file = file_path
                self.resource_loaded = True
                
                # :jp 対応するJSONファイルを読み込み/作成
                # :en Load/create corresponding JSON file
                self.load_or_create_sprite_json(file_path)
                
                print(f"Successfully loaded: {file_path}")
                print("Resource file loaded. You can now view sprites in the image bank.")
            else:
                print(f"File not found: {file_path}")
                
        except Exception as e:
            print(f"Error loading pyxres file: {e}")
            self.resource_loaded = False

    def update(self):
        """
        :jp アプリケーションの状態を更新します。
        :en Update the application state.
        """
        # :jp ダイアログが表示されているか確認
        # :en Check if a dialog is active
        if self.dialog_manager.active_dialog:
            self.dialog_manager.update()
            self.file_open_controller.update()
            self.sprite_edit_controller.update()
            
            # :jp スプライト編集ダイアログの結果をチェック
            # :en Check sprite edit dialog result
            self.check_sprite_edit_result()
            
            return # :jp ダイアログ表示中は他の処理をスキップ # :en Skip other processes while the dialog is displayed

        # :jp ファイルオープンダイアログの結果をチェック
        # :en Check file open dialog result
        self.check_file_open_result()

        # :jp コマンドパレットの更新
        # :en Update the command palette
        self.update_command_palette()
        
        # :jp タイルクリック処理
        # :en Handle tile clicks
        self.handle_tile_click()
        
        # :jp 右クリック処理（スプライト編集）
        # :en Handle right click (sprite editing)
        self.handle_sprite_edit_request()

        # キー入力でスクロール操作（8ピクセル単位）
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.scroll_x = max(0, self.scroll_x - 8)
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.scroll_x = min(16, self.scroll_x + 8)  # 最大スクロール範囲（256 - 240 = 16）
        if pyxel.btnp(pyxel.KEY_UP):
            self.scroll_y = max(0, self.scroll_y - 8)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.scroll_y = min(56, self.scroll_y + 8)  # 最大スクロール範囲（256 - 200 = 56）

        # :jp キーボードショートカット
        # :en Keyboard shortcuts
        if pyxel.btnp(pyxel.KEY_F1):
            self.action_load()
        if pyxel.btnp(pyxel.KEY_F2):
            self.action_toggle_viewport_size()

    def update_command_palette(self):
        """
        :jp コマンドパレットのマウスホバーとクリックを処理します。
        :en Process mouse hover and clicks for the command palette.
        """
        mouse_x, mouse_y = pyxel.mouse_x, pyxel.mouse_y
        for button in self.command_buttons:
            x, y, w, h = button['rect']
            button['is_hover'] = x <= mouse_x < x + w and y <= mouse_y < y + h
            
            if button['is_hover'] and pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                button['action']()

    def draw(self):
        """
        :jp 画面を描画します。
        :en Draw the screen.
        """
        # :jp 画面を黒でクリアします
        # :en Clear the screen with black
        pyxel.cls(pyxel.COLOR_BLACK)



        #pyxel.blt(16, 16, 0, 0, 0, 16, 16, 1, 10, 1)    
    

            # self.x, self.y,
            # # 対応するイメージバンクの番号、x座標、y座標、横サイズ、縦サイズ、透明色
            # 0, self.type * self.size, 0, self.size, self.size+1, 0,
            # # 回転角度(ラジアンでなく度:Degree)、拡大率(1より小さいときは縮小)
            # self.rotate, self.scale)
        
        # :jp コマンドパレットを描画
        # :en Draw the command palette
        self.draw_command_palette()

        # :jp メインコンテンツの描画（常に表示）
        # :en Draw main content (always visible)
        self.draw_main_content()
        
        # :jp ダイアログがアクティブな場合はそれをオーバーレイ
        # :en If a dialog is active, draw it as overlay
        if self.dialog_manager.active_dialog:
            self.dialog_manager.draw()



        #blt(x, y, img, u, v, w, h, [colkey], [rotate], [scale])

    def draw_command_palette(self):
        """
        :jp コマンドパレットのボタンを描画します。
        :en Draw the command palette buttons.
        """
        for button in self.command_buttons:
            x, y, w, h = button['rect']
            
            # :jp ボタンの背景と枠線を描画
            # :en Draw button background and border
            bg_color = pyxel.COLOR_DARK_BLUE if button['is_hover'] else pyxel.COLOR_NAVY
            pyxel.rect(x, y, w, h, bg_color)
            pyxel.rectb(x, y, w, h, pyxel.COLOR_WHITE)
            
            # :jp ボタンのラベルを描画
            # :en Draw button label
            text_x = x + (w - len(button['label']) * pyxel.FONT_WIDTH) / 2
            text_y = y + (h - pyxel.FONT_HEIGHT) / 2
            pyxel.text(int(text_x), int(text_y), button['label'], pyxel.COLOR_WHITE)

    def draw_main_content(self):
        """
        :jp メインコンテンツを描画します
        :en Draw main content
        """
        if self.resource_loaded:
            # :jp リソースファイル情報をコマンドパレットの下に表示
            # :en Display resource file info below command palette
            selected_info = f"Tile: ({self.selected_tile_x},{self.selected_tile_y})" if self.selected_tile_x is not None else "Tile: None"
            info_text = f"Loaded: {os.path.basename(self.loaded_pyxres_file)} | Scroll: ({self.scroll_x},{self.scroll_y}) | {selected_info}"
            pyxel.text(5, 23, info_text, pyxel.COLOR_WHITE)
            
            # :jp スプライトシート表示
            # :en Display sprite sheet
            self.draw_sprite_sheet()
            
        else:
            # :jp リソースファイルが読み込まれていない場合の表示
            # :en Display when no resource file is loaded
            message = "Press F1/LOAD to open file | F2/RESET scroll"
            x = (self.WIDTH - len(message) * pyxel.FONT_WIDTH) / 2
            y = (self.HEIGHT - pyxel.FONT_HEIGHT) / 2
            pyxel.text(int(x), int(y), message, pyxel.COLOR_WHITE)

    def draw_sprite_sheet(self):
        """
        :jp スプライトシートを等倍で描画
        :en Draw sprite sheet at 1x scale
        """
        # 表示領域サイズ（ウィンドウサイズに合わせて調整）
        display_width = 240  # 256 - 16 (余白)
        display_height = 200 # 256 - 56 (上部コマンド領域)
        
        # 背景領域
        pyxel.rect(self.display_x, self.display_y, display_width, display_height, pyxel.COLOR_NAVY)
        
        # 選択されたタイルをハイライト表示（スプライトより先に描画 = 奥に表示）
        self.draw_selected_tile_highlight()
        
        # スプライトシート描画（等倍）
        pyxel.blt(
            self.display_x,          # x: 表示X位置
            self.display_y,          # y: 表示Y位置
            0,                       # img: 画像バンク0
            self.scroll_x,           # u: 切り出し開始X
            self.scroll_y,           # v: 切り出し開始Y
            display_width,           # w: 切り出し幅
            display_height,          # h: 切り出し高さ
            0                        # colkey: 透明色（黒を透明にしない）
        )
        
        # グリッド描画（最前面）
        self.draw_grid(display_width, display_height)
        
        # 選択されたスプライトのNAMEを表示
        self.draw_selected_sprite_name()

    def draw_grid(self, display_width, display_height):
        """
        :jp グリッド線を描画（8ピクセル単位）
        :en Draw grid lines (8 pixel units)
        """
        grid_spacing = 8  # 8ピクセル単位のグリッド
        
        # 垂直線
        for x in range(0, display_width + 1, grid_spacing):
            # スクロール位置に応じてオフセット調整
            offset_x = self.scroll_x % grid_spacing
            line_x = self.display_x + x - offset_x
            
            if self.display_x <= line_x <= self.display_x + display_width:
                pyxel.line(
                    line_x, self.display_y,
                    line_x, self.display_y + display_height,
                    pyxel.COLOR_WHITE
                )
        
        # 水平線
        for y in range(0, display_height + 1, grid_spacing):
            # スクロール位置に応じてオフセット調整
            offset_y = self.scroll_y % grid_spacing
            line_y = self.display_y + y - offset_y
            
            if self.display_y <= line_y <= self.display_y + display_height:
                pyxel.line(
                    self.display_x, line_y,
                    self.display_x + display_width, line_y,
                    pyxel.COLOR_WHITE
                )

    def handle_tile_click(self):
        """
        :jp タイルクリック処理
        :en Handle tile click events
        """
        if not self.resource_loaded:
            return
            
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            mouse_x, mouse_y = pyxel.mouse_x, pyxel.mouse_y
            
            # 表示領域内かチェック
            display_width = 240
            display_height = 200
            if (self.display_x <= mouse_x < self.display_x + display_width and
                self.display_y <= mouse_y < self.display_y + display_height):
                
                # マウス座標をリソースファイル座標系に変換
                relative_x = mouse_x - self.display_x
                relative_y = mouse_y - self.display_y
                
                # リソースファイル上の座標を計算
                resource_x = self.scroll_x + relative_x
                resource_y = self.scroll_y + relative_y
                
                # 8ピクセル単位のタイル座標に変換
                tile_x = (resource_x // 8) * 8
                tile_y = (resource_y // 8) * 8
                
                # 選択状態を更新
                self.selected_tile_x = tile_x
                self.selected_tile_y = tile_y
                
                print(f"Tile selected: ({tile_x}, {tile_y})")

    def draw_selected_tile_highlight(self):
        """
        :jp 選択されたタイルをハイライト表示
        :en Draw highlight for selected tile
        """
        if self.selected_tile_x is None or self.selected_tile_y is None:
            return
        
        # リソース座標系から画面座標系に変換
        screen_x = self.display_x + (self.selected_tile_x - self.scroll_x)
        screen_y = self.display_y + (self.selected_tile_y - self.scroll_y)
        
        # 表示領域内かチェック
        display_width = 240
        display_height = 200
        if (screen_x >= self.display_x and screen_x < self.display_x + display_width - 8 and
            screen_y >= self.display_y and screen_y < self.display_y + display_height - 8):
            
            # YELLOWで8x8のハイライト枠を描画（グリッド線上に表示）
            pyxel.rectb(screen_x - 1, screen_y - 1, 8 + 3, 8 + 3, pyxel.COLOR_YELLOW)

    def load_or_create_sprite_json(self, pyxres_file):
        """
        :jp pyxresファイルに対応するJSONファイルを読み込み、存在しない場合のみ_template.jsonから作成
        :en Load JSON file corresponding to pyxres file, create from _template.json only if not exists
        """
        # JSONファイル名を生成（拡張子を .pyxres から .json に変更）
        json_file = os.path.splitext(pyxres_file)[0] + '.json'
        self.sprite_json_file = json_file
        
        try:
            if os.path.exists(json_file):
                # 既存のJSONファイルを読み込み
                with open(json_file, 'r', encoding='utf-8') as f:
                    self.sprite_data = json.load(f)
                print(f"Loaded existing sprite definitions: {json_file}")
                
                # _primary_ からフィールド定義を取得してダイアログコントローラーに設定
                self.update_dialog_fields_from_template()
                
            else:
                # JSONファイルが存在しない場合のみ、_template.jsonから作成
                self.sprite_data = self.create_initial_sprite_json(pyxres_file)
                self.save_sprite_json()
                print(f"Created new sprite definitions from template: {json_file}")
                
                # _primary_ からフィールド定義を取得してダイアログコントローラーに設定
                self.update_dialog_fields_from_template()
                
        except Exception as e:
            print(f"Error loading/creating sprite JSON: {e}")
            # エラー時は初期化状態で作成
            self.sprite_data = self.create_initial_sprite_json(pyxres_file)
            self.update_dialog_fields_from_template()

    def create_initial_sprite_json(self, pyxres_file):
        """
        :jp _template.jsonをコピーして初期化状態のスプライトJSONファイルを作成
        :en Create initial sprite JSON file by copying _template.json
        """
        template_file = os.path.join(os.path.dirname(__file__), '_template.json')
        json_file = os.path.splitext(pyxres_file)[0] + '.json'
        
        try:
            # テンプレートファイルをコピー
            shutil.copy2(template_file, json_file)
            
            # コピーしたファイルを読み込み、resource_fileのみ変更
            with open(json_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # resource_fileを選択されたpyxresファイル名に変更
            template_data["meta"]["resource_file"] = os.path.basename(pyxres_file)
            
            # _primary_ は特殊グループとして保持（削除しない）
            # 変更されたデータを保存
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            return template_data
            
        except Exception as e:
            print(f"Error copying template file: {e}")
            # テンプレートファイル処理に失敗した場合のフォールバック
            return {
                "meta": {
                    "sprite_size": 8,
                    "resource_file": os.path.basename(pyxres_file),
                    "created_by": "SpriteDefiner",
                    "version": "3.0"
                },
                "sprites": {
                    "_primary_": {
                        "x": 0,
                        "y": 0,
                        "NAME": "SpriteName",
                        "ACT_NAME": "ActionName",
                        "ANIM_NUMBER": "Animation Number",
                        "ENPTY01": "Reserved Field",
                        "ENPTY02": "Reserved Field",
                        "ENPTY03": "Reserved Field",
                        "ENPTY04": "Reserved Field",
                        "ENPTY05": "Reserved Field",
                        "ENPTY06": "Reserved Field",
                        "ENPTY07": "Reserved Field",
                        "ENPTY08": "Reserved Field",
                        "ENPTY09": "Reserved Field",
                        "ENPTY10": "Reserved Field"
                    }
                }
            }

    def save_sprite_json(self):
        """
        :jp スプライトJSONファイルを保存
        :en Save sprite JSON file
        """
        if self.sprite_data and self.sprite_json_file:
            try:
                with open(self.sprite_json_file, 'w', encoding='utf-8') as f:
                    json.dump(self.sprite_data, f, indent=2, ensure_ascii=False)
                print(f"Saved sprite definitions: {self.sprite_json_file}")
            except Exception as e:
                print(f"Error saving sprite JSON: {e}")

    def add_sprite_at_position(self, x, y):
        """
        :jp 指定座標にスプライトを追加（_primary_の構造を参考に作成）
        :en Add sprite at specified position (using _primary_ structure as reference)
        """
        if not self.sprite_data:
            return
            
        sprite_key = f"{x}_{y}"
        
        # _primary_ の構造を参考に新しいスプライトを作成
        if "_primary_" in self.sprite_data["sprites"]:
            template_sprite = self.sprite_data["sprites"]["_primary_"]
            new_sprite = template_sprite.copy()  # 全フィールドをコピー
            
            # 座標のみ更新
            new_sprite["x"] = x
            new_sprite["y"] = y
            
            # スプライトを追加
            self.sprite_data["sprites"][sprite_key] = new_sprite
            
            # JSONファイルに保存
            self.save_sprite_json()
            
            print(f"Added sprite at ({x}, {y}) with template structure")
        else:
            print("Error: _primary_ not found in sprite data")

    def update_all_sprites_structure(self):
        """
        :jp _primary_の構造変更時に全スプライトの構造を同期
        :en Synchronize all sprite structures when _primary_ structure changes
        """
        if not self.sprite_data or "_primary_" not in self.sprite_data["sprites"]:
            return
            
        template_sprite = self.sprite_data["sprites"]["_primary_"]
        
        # 全スプライト（_primary_以外）の構造を更新
        for sprite_key, sprite_data in self.sprite_data["sprites"].items():
            if sprite_key != "_primary_":
                # 座標情報を保持
                x = sprite_data.get("x", 0)
                y = sprite_data.get("y", 0)
                
                # テンプレート構造をコピー
                updated_sprite = template_sprite.copy()
                
                # 座標を復元
                updated_sprite["x"] = x
                updated_sprite["y"] = y
                
                # 更新
                self.sprite_data["sprites"][sprite_key] = updated_sprite
        
        # 変更を保存
        self.save_sprite_json()
        print("Updated all sprites to match template structure")

    def get_sprite_at_position(self, x, y):
        """
        :jp 指定座標のスプライト情報を取得
        :en Get sprite information at specified position
        """
        if not self.sprite_data:
            return None
            
        sprite_key = f"{x}_{y}"
        return self.sprite_data["sprites"].get(sprite_key, None)

    def handle_sprite_edit_request(self):
        """
        :jp 選択されたスプライト上での右クリックを処理してプロパティ編集ダイアログを表示
        :en Handle right click on selected sprite to show property edit dialog
        """
        if not self.resource_loaded or self.selected_tile_x is None or self.selected_tile_y is None:
            return
            
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            mouse_x, mouse_y = pyxel.mouse_x, pyxel.mouse_y
            
            # マウス座標をリソース座標系に変換
            display_width = 240
            display_height = 200
            if (self.display_x <= mouse_x < self.display_x + display_width and
                self.display_y <= mouse_y < self.display_y + display_height):
                
                relative_x = mouse_x - self.display_x
                relative_y = mouse_y - self.display_y
                resource_x = self.scroll_x + relative_x
                resource_y = self.scroll_y + relative_y
                tile_x = (resource_x // 8) * 8
                tile_y = (resource_y // 8) * 8
                
                # 選択されたタイル上での右クリックかチェック
                if tile_x == self.selected_tile_x and tile_y == self.selected_tile_y:
                    self.show_sprite_edit_dialog(tile_x, tile_y)

    def show_sprite_edit_dialog(self, x, y):
        """
        :jp スプライトプロパティ編集ダイアログを表示
        :en Show sprite property edit dialog
        """
        sprite_key = f"{x}_{y}"
        
        # 既存スプライトがあるかチェック、なければテンプレートから作成
        if sprite_key not in self.sprite_data["sprites"]:
            self.add_sprite_at_position(x, y)
        
        sprite_info = self.sprite_data["sprites"][sprite_key]
        
        print(f"Opening sprite editor for ({x}, {y}):")
        print(f"Current properties: {sprite_info}")
        
        # スプライト編集ダイアログを表示
        self.sprite_edit_controller.show_sprite_edit_dialog(sprite_info)
        print(f"Opened sprite editor for ({x}, {y})")

    def check_sprite_edit_result(self):
        """
        :jp スプライト編集ダイアログの結果をチェックし、変更を適用
        :en Check sprite edit dialog result and apply changes
        """
        if not self.sprite_edit_controller.is_active():
            result_data = self.sprite_edit_controller.get_result()
            
            if result_data and result_data["result"] == "OK" and result_data["data"]:
                # 編集されたデータを適用
                edited_data = result_data["data"]
                x = edited_data.get("x", 0)
                y = edited_data.get("y", 0)
                sprite_key = f"{x}_{y}"
                
                # スプライトデータを更新
                if sprite_key in self.sprite_data["sprites"]:
                    self.sprite_data["sprites"][sprite_key].update(edited_data)
                    
                    # JSONファイルに保存
                    self.save_sprite_json()
                    
                    print(f"Updated sprite at ({x}, {y})")
                    print(f"New properties: {edited_data}")
                else:
                    print(f"Error: Sprite {sprite_key} not found")
            
            elif result_data and result_data["result"] == "CANCEL":
                print("Sprite edit canceled")

    def draw_selected_sprite_name(self):
        """
        :jp 選択されたスプライトのNAMEをグリッドの下に表示
        :en Display the NAME of selected sprite below the grid
        """
        if (not self.resource_loaded or 
            self.selected_tile_x is None or 
            self.selected_tile_y is None or
            not self.sprite_data):
            return
            
        # 選択されたタイルのスプライト情報を取得
        sprite_info = self.get_sprite_at_position(self.selected_tile_x, self.selected_tile_y)
        
        if sprite_info and "NAME" in sprite_info:
            sprite_name = sprite_info["NAME"]
            
            # テンプレート初期値の場合は空文字として扱う
            if sprite_name in ["Reserved Field", "SpriteName", "ActionName", "Animation Number"]:
                sprite_name = "(No Name)"
            
            # グリッドの下に表示（y座標 = display_y + display_height + 5）
            display_height = 200
            text_y = self.display_y + display_height + 5
            text_x = self.display_x
            
            # 背景を描画して見やすくする
            text_width = len(f"Selected: {sprite_name}") * pyxel.FONT_WIDTH
            pyxel.rect(text_x, text_y, text_width + 4, pyxel.FONT_HEIGHT + 2, pyxel.COLOR_NAVY)
            
            # テキストを描画
            pyxel.text(text_x + 2, text_y + 1, f"Selected: {sprite_name}", pyxel.COLOR_WHITE)
        else:
            # スプライト情報がない場合
            display_height = 200
            text_y = self.display_y + display_height + 5
            text_x = self.display_x
            
            sprite_key = f"{self.selected_tile_x}_{self.selected_tile_y}"
            text_width = len(f"Selected: {sprite_key} (No Data)") * pyxel.FONT_WIDTH
            pyxel.rect(text_x, text_y, text_width + 4, pyxel.FONT_HEIGHT + 2, pyxel.COLOR_NAVY)
            
            pyxel.text(text_x + 2, text_y + 1, f"Selected: {sprite_key} (No Data)", pyxel.COLOR_WHITE)

    def update_dialog_fields_from_template(self):
        """
        :jp _primary_ からフィールド定義を取得してダイアログコントローラーに設定
        :en Get field definitions from _primary_ and set to dialog controller
        """
        if not self.sprite_data or "_primary_" not in self.sprite_data.get("sprites", {}):
            print("Warning: _primary_ not found in sprite data")
            return
            
        template_data = self.sprite_data["sprites"]["_primary_"]
        
        # x, y以外のフィールドを取得してfield_mappingsを動的に構築
        field_mappings = {}
        field_names = [key for key in template_data.keys() if key not in ["x", "y"]]
        
        # dialogs.jsonの固定ウィジェットIDとの対応（順序ベース）
        fixed_widget_ids = [
            "IDC_SPRITE_NAME",   # NAME用
            "IDC_ACT_NAME",      # ACT_NAME用  
            "IDC_ANIM_NUMBER",   # ANIM_NUMBER用
            "IDC_ENPTY01",       # 4番目のフィールド用
            "IDC_ENPTY02",       # 5番目のフィールド用
            "IDC_ENPTY03",       # 6番目のフィールド用
            "IDC_ENPTY04",       # 7番目のフィールド用
            "IDC_ENPTY05",       # 8番目のフィールド用
            "IDC_ENPTY06",       # 9番目のフィールド用
            "IDC_ENPTY07",       # 10番目のフィールド用
            "IDC_ENPTY08",       # 11番目のフィールド用
            "IDC_ENPTY09",       # 12番目のフィールド用
            "IDC_ENPTY10"        # 13番目のフィールド用
        ]
        
        # フィールド名を固定ウィジェットIDに順序ベースでマッピング
        for i, field_name in enumerate(field_names):
            if i < len(fixed_widget_ids):
                field_mappings[field_name] = fixed_widget_ids[i]
        
        # ダイアログコントローラーにフィールドマッピングを設定
        self.sprite_edit_controller.field_mappings = field_mappings
        
        print(f"Updated dialog fields from template: {list(field_mappings.keys())}")


if __name__ == "__main__":
    SpriteDefiner()