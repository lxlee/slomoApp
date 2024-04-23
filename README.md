### SlomoApp
a simple wrapper gui for [slomo](https://github.com/avinashpaliwal/Super-SloMo) and [flubber](https://github.com/veltman/flubber.git) to smoothly interpolating between 2-D shapes for specifical usage.

### build
```bash
python3 ./setup.py bdist_wheel
```

### install
```bash
pip install dist/Slomo-1.0.0-py3-none-any.whl
```

### requires
```bash
'torch >= 2.0.1',
'torchvision',
'svg.path',
'pypotrace',
'scipy',
'numpy',
'CairoSVG',
'pillow',
'customtkinter',
'CTkMessagebox',
'click'
```

### attention
It is recommanded to run in conda environments.  


To install pypotrace, you may need to run the following [commands](https://pypi.org/project/pypotrace/)
```bash
apt-get install build-essential python-dev libagg-dev libpotrace-dev pkg-config
```

### usage
```bash
# gui
slomo  

# command 
slomoCMD --help
```
