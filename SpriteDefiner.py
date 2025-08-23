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

# :jp SpriteDefinerDlgモジュールへのパスを追加
# :en Add the path to the SpriteDefinerDlg module
sys.path.append(os.path.join(os.path.dirname(__file__), 'SpriteDefinerDlg'))

from dialog_manager import DialogManager
from file_open_dialog import FileOpenDialogController
from viewport_config import ViewportConfig
from viewport_renderer import ViewportRenderer

class SpriteDefiner:
    def __init__(self):
        # :jp ウィンドウ設定
        # :en Window settings
        self.WIDTH = 450
        self.HEIGHT = 400

        # :jp Pyxelを初期化
        # :en Initialize Pyxel
        pyxel.init(self.WIDTH, self.HEIGHT, title="SpriteDefiner Ver.2", quit_key=pyxel.KEY_Q, display_scale=2)

        # :jp DialogManagerを初期化
        # :en Initialize DialogManager
        dialogs_json_path = os.path.join(os.path.dirname(__file__), 'SpriteDefinerDlg', 'dialogs.json')
        self.dialog_manager = DialogManager(dialogs_json_path)

        # :jp FileOpenDialogControllerを初期化
        # :en Initialize FileOpenDialogController
        self.file_open_controller = FileOpenDialogController(self.dialog_manager, ".")

        # :jp 読み込まれたリソースファイル情報
        # :en Loaded resource file information
        self.loaded_pyxres_file = None
        self.resource_loaded = False

        # :jp ビューポートシステムを初期化
        # :en Initialize viewport system
        self.viewport_config = ViewportConfig()
        self.viewport_renderer = ViewportRenderer(self.viewport_config)

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
            {'label': 'SIZE(F2)', 'key': pyxel.KEY_F2, 'action': self.action_toggle_viewport_size},
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
        :jp SIZEアクション（ビューポートサイズ切り替え）
        :en SIZE action (toggles viewport size)
        """
        # 基本サイズをローテーション: 64 → 128 → 192 → 64
        current_size = self.viewport_config.viewport_size
        if current_size == 64:
            self.viewport_config.set_viewport_size(128)
        elif current_size == 128:
            self.viewport_config.set_viewport_size(192)
        else:
            self.viewport_config.set_viewport_size(64)

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
            return # :jp ダイアログ表示中は他の処理をスキップ # :en Skip other processes while the dialog is displayed

        # :jp ファイルオープンダイアログの結果をチェック
        # :en Check file open dialog result
        self.check_file_open_result()

        # :jp コマンドパレットの更新
        # :en Update the command palette
        self.update_command_palette()

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

        # :jp コマンドパレットを描画
        # :en Draw the command palette
        self.draw_command_palette()

        # :jp ダイアログがアクティブな場合はそれを描画
        # :en If a dialog is active, draw it
        if self.dialog_manager.active_dialog:
            self.dialog_manager.draw()
        else:
            # :jp メインコンテンツの描画
            # :en Draw main content
            self.draw_main_content()

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
            # :jp リソースファイルが読み込まれている場合
            # :en Display when resource file is loaded
            pyxel.text(10, 30, f"Loaded: {os.path.basename(self.loaded_pyxres_file)}", pyxel.COLOR_WHITE)
            
            # :jp ビューポートでスプライトシート表示
            # :en Display sprite sheet with viewport
            self.viewport_renderer.draw_sprite_viewport(0)  # Image bank 0
            self.viewport_renderer.draw_viewport_grid(False)  # Not in edit mode
            
            # :jp デバッグ情報表示
            # :en Display debug information
            self.viewport_renderer.draw_debug_info()
            
        else:
            # :jp リソースファイルが読み込まれていない場合の表示
            # :en Display when no resource file is loaded
            message = "Press F1 or click LOAD(F1) to open file dialog."
            x = (self.WIDTH - len(message) * pyxel.FONT_WIDTH) / 2
            y = (self.HEIGHT - pyxel.FONT_HEIGHT) / 2
            pyxel.text(int(x), int(y), message, pyxel.COLOR_WHITE)

if __name__ == "__main__":
    SpriteDefiner()