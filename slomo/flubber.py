import os
import potrace
from .interpolate import interpolate
import numpy as np
from PIL import Image
from scipy import ndimage
from cairosvg import svg2png
from xml.dom import minidom

def pngToSvg(pngfile, svgfile):
    gray_image = Image.open(pngfile).convert("L")
    arr = np.asarray(gray_image).copy()
    arr[arr < 1] = 0
    arr[arr >= 1] = 1

    arr = ndimage.binary_fill_holes(arr)
    # print(arr.dtype, arr.max(), arr.min())

    trace = potrace.Bitmap(arr)
    curve_paths = trace.trace(turdsize=2)

    with open(svgfile, 'w') as f:
        f.write(
            f'''<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{gray_image.width}" height="{gray_image.height}" viewBox="0 0 {gray_image.width} {gray_image.height}">''')
    
        parts = []
        for curve in curve_paths:
            sp_x, sp_y = curve.start_point
            parts.append(f"M{sp_x:.02f},{sp_y:.02f}")
            # print(svgfile, len(curve.segments))
            for segment in curve:
                if segment.is_corner:
                    c_x, c_y = segment.c
                    e_x, e_y = segment.end_point
                    parts.append(f"L{c_x:.02f},{c_y:.02f}L{e_x:.02f},{e_y:.02f}")
                else:
                    c1_x, c1_y = segment.c1
                    c2_x, c2_y = segment.c2
                    e_x, e_y = segment.end_point
                    parts.append(f"C{c1_x:.02f},{c1_y:.02f} {c2_x:.02f},{c2_y:.02f} {e_x:.02f},{e_y:.02f}")
            parts.append("z")
        # print("Total points ", len(parts))
        f.write(f'<path  d="{"".join(parts)}"/>')
        f.write("</svg>")

TempDir = "/tmp"

class Flubber:
    def __init__(self, sf=2) -> None:
        self._sf = sf

    def process(self, firstImage, secondImage, dstDir):
        outputPath = dstDir
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)

        try:
            firstSvg = os.path.join(TempDir, os.path.splitext(os.path.basename(firstImage))[0] + ".svg")
            pngToSvg(firstImage, firstSvg)

            secondSvg = os.path.join(TempDir, os.path.splitext(os.path.basename(secondImage))[0] + ".svg")
            pngToSvg(secondImage, secondSvg)

            svg0 = minidom.parse(firstSvg)
            svg1 = minidom.parse(secondSvg)

            path0 = svg0.getElementsByTagName("path")[0].getAttribute('d')
            path1 = svg1.getElementsByTagName("path")[0].getAttribute('d')

            if not path0 or not path1:
                print("No path found in svg, ignore")
                return

            interpolator = interpolate(path0, path1, {"maxSegmentLength":1})

            pathEle = svg0.getElementsByTagName("path")[0]

            for inx in range(self._sf + 1): 
                res = interpolator(inx / (self._sf + 1)) 

                pathEle.setAttribute('d', res)

                writeFile = f"{outputPath}/{inx:03d}.png"
                svg2png(svg0.toprettyxml(), write_to=writeFile)
                img = np.asarray(Image.open(writeFile))
                Image.fromarray(img[:,:,3]).save(writeFile) # save alpha channel only
        finally:
            if os.path.exists(firstSvg): os.remove(firstSvg)
            if os.path.exists(secondSvg): os.remove(secondSvg)
