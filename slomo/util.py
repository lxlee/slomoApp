import math

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def perimeter(points:list):
    if len(points) < 1:
        return 0
    
    peri = 0
    for i in range(len(points)):
        peri += distance(points[i - 1], points[i])
    return peri

def pointAlong(a, b, pct):
    return (a[0] + (b[0] - a[0]) * pct, a[1] + (b[1] - a[1]) * pct)

'''
 * Returns the signed area of the specified polygon. If the vertices of the polygon are in counterclockwise order
 * (assuming a coordinate system where the origin <0,0> is in the top-left corner), the returned area is positive;
 * otherwise it is negative, or zero.
 *
 * @param polygon Array of coordinates <x0, y0>, <x1, y1> and so on.
 */
'''
def polygonArea(points:list):
    area = 0 
    for inx in range(len(points)):
        a = points[inx - 1]
        b = points[inx]
        area += a[1] * b[0] - a[0] * b[1]

    return area / 2

def boundingbox(points:list):
    x_coords = []
    y_coords = []

    for point in points:
        x_coords.append(point[0])
        y_coords.append(point[1])

    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    return [x_min, y_min, x_max, y_max]


def linePointY(p1, p2, x):
    a = (p1[1] - p2[1]) / (p1[0] - p2[0])
    b = (p1[0] * p2[1] - p2[0] * p1[1]) / (p1[0] - p2[0])
    return a * x + b
