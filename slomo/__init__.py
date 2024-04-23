from .slomo import Slomo, get_device_list
from .flubber import Flubber
from .app import App

def main():
    app = App()
    app.mainloop()


__all__ = ["main", "Slomo", "get_device_list", "Flubber"]
