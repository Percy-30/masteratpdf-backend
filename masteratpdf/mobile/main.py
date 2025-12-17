
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class MobileApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        label = Label(text="MasterAtPDF Mobile Client")
        layout.add_widget(label)
        return layout

if __name__ == '__main__':
    MobileApp().run()
