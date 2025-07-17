from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.icon_definitions import md_icons
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from kivymd.uix.list import OneLineIconListItem

KV = '''
<IconItem>:
    IconLeftWidget:
        icon: root.icon

<IconScreen>:
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: "KivyMD Icons"
            elevation: 2

        MDTextField:
            id: search_field
            hint_text: "Search icon"
            mode: "rectangle"
            size_hint_x: 0.9
            pos_hint: {"center_x": 0.5}
            on_text: root.update_icons(self.text)

        RecycleView:
            id: rv
            viewclass: "IconItem"
            scroll_type: ['bars', 'content']
            bar_width: dp(10)

            RecycleBoxLayout:
                default_size: None, dp(56)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
'''

Builder.load_string(KV)


class IconItem(OneLineIconListItem):
    icon = StringProperty()


class IconScreen(MDScreen):
    def on_kv_post(self, base_widget):
        self.full_icon_list = list(md_icons.keys())
        self.update_icons("")

    def update_icons(self, search_text):
        search_text = search_text.lower()
        filtered = [
            {"text": name, "icon": name}
            for name in self.full_icon_list
            if search_text in name.lower()
        ]
        self.ids.rv.data = filtered


class MainApp(MDApp):
    def build(self):
        return IconScreen()


MainApp().run()
