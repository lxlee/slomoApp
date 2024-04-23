import os
import glob
from typing import Union, Tuple, Optional

import tkinter
import customtkinter
from CTkMessagebox import CTkMessagebox
import threading
import slomo

# System Settings
customtkinter.set_appearance_mode("light")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self, fg_color: Optional[Union[str, Tuple[str, str]]] = None, **kwargs):
        super().__init__(fg_color, **kwargs)

        self._init_base_gui()

        def _addEntry(label, placehold_text, row=0):
            title = customtkinter.CTkLabel(self._contentFrame, text="文件路径")
            title.grid(row=row, column=0, sticky='e', padx=5)
            entry = customtkinter.CTkEntry(self._contentFrame, placeholder_text="源文件夹路径")
            entry.grid(row=row, column=1, columnspan=3, padx=10, sticky="we")

            def __select_directory():
                directory = customtkinter.filedialog.askdirectory()
                if directory and os.path.exists(directory):
                    entry.delete(0, customtkinter.END)
                    entry.insert(0, directory)

            btn = customtkinter.CTkButton(self._contentFrame, text="...", command=__select_directory)
            btn.grid(row=row, column=4, sticky='w', padx=5)
            return entry

        self.sEntry = _addEntry("源文件夹路径", "源文件夹路径", row=0)
        self.dEntry = _addEntry("源文件夹路径", "源文件夹路径", row=1)

        tmpFrame = customtkinter.CTkFrame(master=self._contentFrame)
        tmpFrame.grid(row=2, column=1, sticky="nwes", padx=5)
        tmpFrame.rowconfigure(0, weight=1)
        tmpFrame.columnconfigure(0, weight=1)
        tmpFrame.columnconfigure(1, weight=2)
        label = customtkinter.CTkLabel(tmpFrame, text="方法")
        label.grid(row=0, column=0, sticky='nswe', padx=2)
        self.methodCombo = customtkinter.CTkComboBox(tmpFrame, values=["slomo", "flubber"])
        self.methodCombo.grid(row=0, column=1, sticky='w', padx=2)

        tmpFrame = customtkinter.CTkFrame(master=self._contentFrame)
        tmpFrame.grid(row=2, column=2, sticky="nwes", padx=5)
        tmpFrame.rowconfigure(0, weight=1)
        tmpFrame.columnconfigure(0, weight=1)
        tmpFrame.columnconfigure(1, weight=1)
        label = customtkinter.CTkLabel(tmpFrame, text="慢放系数")
        label.grid(row=0, column=0, sticky='nswe', padx=2)
        self.sfEntry = customtkinter.CTkEntry(tmpFrame, placeholder_text="slomo factor(int)")
        self.sfEntry.grid(row=0, column=1, sticky='w', padx=2)

        tmpFrame = customtkinter.CTkFrame(master=self._contentFrame)
        tmpFrame.grid(row=2, column=3, sticky="nwes", padx=5)
        tmpFrame.rowconfigure(0, weight=1)
        tmpFrame.columnconfigure(0, weight=1)
        tmpFrame.columnconfigure(1, weight=1)
        label = customtkinter.CTkLabel(tmpFrame, text="运行设备")
        label.grid(row=0, column=0, sticky='nswe', padx=2)
        self.combobox = customtkinter.CTkComboBox(tmpFrame, values=slomo.get_device_list())
        self.combobox.grid(row=0, column=1, sticky='w', padx=2)

        btn = customtkinter.CTkButton(self._contentFrame, text="确定", command=self._interlace)
        btn.grid(row=3, columnspan=5)

        self.pLabel = customtkinter.CTkLabel(self._progressFrame, text="0%")
        self.pLabel.grid(row=0, column=3, sticky='w')
        self.progressBar = customtkinter.CTkProgressBar(self._progressFrame, width=400)
        self.progressBar.grid(row=0, column=1, columnspan=2, sticky='we', padx=5)
        self.progressBar.set(0.0)

    def _init_base_gui(self):
        self.geometry("800x480")
        self.resizable(False, False)
        self.title("Super-Slomo插帧")

        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._contentFrame = customtkinter.CTkFrame(master=self)
        self._contentFrame.grid(row=0, column=0, sticky="nwes")
        self._contentFrame.grid_columnconfigure(0, weight=1)    
        self._contentFrame.grid_columnconfigure(1, weight=2) 
        self._contentFrame.grid_columnconfigure(2, weight=2) 
        self._contentFrame.grid_columnconfigure(3, weight=2)
        self._contentFrame.grid_columnconfigure(4, weight=1) 
        self._contentFrame.grid_rowconfigure(0, weight=1)
        self._contentFrame.grid_rowconfigure(1, weight=1)
        self._contentFrame.grid_rowconfigure(2, weight=1)
        self._contentFrame.grid_rowconfigure(3, weight=2)

        self._progressFrame = customtkinter.CTkFrame(master=self)
        self._progressFrame.grid(row=1, column=0, sticky="nwes")
        self._progressFrame.rowconfigure(1, weight=1)
        self._progressFrame.columnconfigure(0, weight=1)
        self._progressFrame.columnconfigure(1, weight=2)
        self._progressFrame.columnconfigure(2, weight=2)
        self._progressFrame.columnconfigure(3, weight=1)

    def _interlace(self):
        srcDir = self.sEntry.get()
        dstDir = self.dEntry.get()
        if not srcDir or not dstDir:
            CTkMessagebox(self, title="提示", message="源文件夹和目的文件夹不能为空")
            return
        
        try:
            sf = int(self.sfEntry.get())
            if sf < 2:
                raise ValueError("sf less than 2")
        except Exception as e:
            CTkMessagebox(self, title="提示", message="慢放倍数必须是大于等于2的整数")
            return
        
        pngs = glob.glob(f"{srcDir}/**/*.png", recursive=True) + glob.glob(f"{srcDir}/**/*.jpg", recursive=True)
        pngs.sort()

        if len(pngs) < 2:
            CTkMessagebox(self, title="提示", message="源文件下png/jpg图片太少")
            return

        thread = threading.Thread(target=self.async_handle, args=(pngs, dstDir, self.methodCombo.get(), sf, self.combobox.get()))
        thread.setDaemon(True)
        thread.start()
        # slm = slomo.Slomo("SuperSloMo39.ckpt", sf, self.combobox.get())
        # for i in range(len(pngs) - 1):
        #     slm.process(pngs[i], pngs[i + 1], os.path.join(dstDir, f"{i:04d}-{i+1:04d}"))

    def _enableWidget(self, widget:customtkinter.CTkBaseClass):
        if isinstance(widget, customtkinter.CTkFrame):
            for child in widget.winfo_children():
                self._enableWidget(child)
        else:
            widget.configure(state="normal")

    def _disableWidget(self, widget:customtkinter.CTkBaseClass):
        if isinstance(widget, customtkinter.CTkFrame):
            for child in widget.winfo_children():
                self._disableWidget(child)
        else:
            widget.configure(state="disabled")

    def _setProcess(self, p:float):
        self.pLabel.configure(text=f"{p * 100:.0f}%")
        self.progressBar.set(p)

    def async_handle(self, pngs, dstDir, method, sf, device):
        try:
            self._disableWidget(self._contentFrame)
            self._setProcess(0)

            path = os.path.realpath(os.path.abspath(__file__))

            if "slomo" == method:
                slm = slomo.Slomo(os.path.join(os.path.dirname(path), "models", "SuperSloMo39.ckpt"), sf, device)
                length = len(pngs) - 1
                for i in range(length):
                    slm.process(pngs[i], pngs[i + 1], os.path.join(dstDir, f"{i:04d}-{i+1:04d}"))

                    p = (i + 1) / length
                    self._setProcess(p)
            elif "flubber" == method:
                flubber = slomo.Flubber(sf)
                length = len(pngs) - 1
                for i in range(length):
                    flubber.process(pngs[i], pngs[i + 1], os.path.join(dstDir, f"{i:04d}-{i+1:04d}"))

                    p = (i + 1) / length
                    self._setProcess(p)

        except Exception as e:
            print(e)
            CTkMessagebox(self, title="提示", message="程序运行出错，请在终端调试")
        finally:
            self._enableWidget(self._contentFrame)