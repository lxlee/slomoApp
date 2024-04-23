#!/usr/bin/env python3

import math
from .util import *
from svg.path import parse_path


INVALID_TYPE='Invalid input type'

def cutPathToRing(path, maxSegmentLength):
    length = path.length()
    numPoints = math.ceil(length / maxSegmentLength)

    points = []
    for inx in range(numPoints):
        percent = inx / numPoints
        p = path.point(percent)
        points.append((p.real, p.imag))

    return points;

def pathStringToRing(string, maxSegmentLength):
    parsed = parse_path(string);
    
    return cutPathToRing(parsed, maxSegmentLength)

def toPathString(points:list):
    strList = [f"{point[0]},{point[1]}" for point in points]
    return "M" + 'L'.join(strList) + "Z"

def normalizeRing(ring, maxSegmentLength):
    if isinstance(ring, str):
        points = pathStringToRing(ring, maxSegmentLength);
    # elif isinstance(ring) == "list":
    else:
        raise TypeError(INVALID_TYPE);

    # check the first point and the last point.
    if distance(points[0], points[-1]) < 1e-6:
        points.pop(-1)

    if len(points) < 2:
        raise ValueError("Input is too native")

    if polygonArea(points) > 0:
        points.reverse() # reverse, make it in counterclockwise order

    return points

def addPoints(ring:list, numPoints:int):
    if numPoints < 1:
        return
    
    desiredLength = len(ring) + numPoints
    step = perimeter(ring) /numPoints

    inx, cursor, insertAt = 0, 0, step / 2
    while(len(ring) < desiredLength):
        p1 = ring[inx]
        p2 = ring[(inx + 1) % len(ring)]
        segment = distance(p1, p2)

        if insertAt < cursor + segment:
            ring.insert(inx + 1, pointAlong(p1, p2, (insertAt - cursor) / segment))
            insertAt += step
            continue

        cursor += segment
        inx += 1

# rotate ring to make the sum of distance of corresponding point in ring and vs smaller
def rotate(ring, vs):
    length = len(ring)
    bestOffset = 0
    minSum = float('inf')

    def _loopDistance(offset):
        nonlocal minSum, bestOffset
        sumOfSquare = 0
        for i, point in enumerate(vs):
            dis = distance(ring[(offset + i) % length], point)
            sumOfSquare += dis
        if sumOfSquare < minSum:
            minSum = sumOfSquare
            bestOffset = offset

    for inx in range(len(ring)):
        _loopDistance(inx)
    
    if bestOffset > 0:
        ring = ring[bestOffset:] + ring[:bestOffset]

    return ring

def interpolatePoints(fromRing, toRing, retString):
    def interpolatePoint(t):  # time value between 0.0 and 1.0
        t = min(max(t, 0.0), 1.0)
        interPoints = [(pair[0][0] + t * (pair[1][0] - pair[0][0]), pair[0][1] + t * (pair[1][1] - pair[0][1])) for pair in zip(fromRing, toRing)]
        return toPathString(interPoints) if retString else interPoints

    return interpolatePoint

def interpolateRing(fromRing, toRing, retString):
    diffNum = len(fromRing) - len(toRing)

    # TODO bisect and add points in one step?
    if diffNum < 0: addPoints(fromRing, abs(diffNum))
    elif diffNum > 0: addPoints(toRing, abs(diffNum))

    fromRing = rotate(fromRing, toRing)

    return interpolatePoints(fromRing, toRing, retString)


def split(points, weights=[]):
    bbox = boundingbox(points)
    splitXs = []
    for inx in range(len(weights)):
        splitXs.append((bbox[2] - bbox[0]) * sum(weights[:inx+1]) + bbox[0])

    allPoints = []
    for inx,point in enumerate(points):
        for value in splitXs:
            if point[0] < value and points[inx-1][0] > value:
                allPoints.append((value, linePointY(point, points[inx-1], value)))
                allPoints.append(point)
                break
            elif point[0] > value and points[inx-1][0] < value:
                allPoints.append((value, linePointY(point, points[inx-1], value)))
                allPoints.append(point)
                break
            elif point[0] <= value:
                allPoints.append(point)
                break

    retPoints = [[] for _ in weights]
    for ini, point in enumerate(allPoints):
        for inj,value in enumerate(splitXs):
            if point[0] < value:
                retPoints[inj].append(point)
                if point[0] == value:
                    if inj + 1 < len(retPoints):
                        retPoints[inj+1].append(point)

    return retPoints

def cut(fromshapes, toshapes, maxSegmentLength):
    fromPoints = [ normalizeRing(shape, maxSegmentLength) for shape in fromshapes ]
    toPoints = [ normalizeRing(shape, maxSegmentLength) for shape in toshapes ]

    def _sortKey(points):
        bbox = boundingbox(points)
        return bbox[0] + bbox[2]

    fromPoints.sort(key=_sortKey)
    toPoints.sort(key=_sortKey)

    if len(fromPoints) > len(toPoints):
        extra = len(fromPoints) - len(toPoints)
        areas = [abs(polygonArea(points)) for points in fromPoints[-1 * extra - 1:]] 
        weights = [area / sum(areas) for area in areas]
        toPoints = toPoints[:-1] + split(toPoints[-1], weights)
    elif len(fromPoints) < len(toPoints):
        extra = len(toPoints) - len(fromPoints)
        areas = [abs(polygonArea(points)) for points in toPoints[-1 * extra - 1:]] 
        weights = [area / sum(areas) for area in areas]
        fromPoints = fromPoints[:-1] + split(fromPoints[-1], weights)

    return (fromPoints, toPoints)


def interpolate(fromShape, toShape, params:dict={ "maxSegmentLength":10, "retString":True }):
    maxSegmentLength = params["maxSegmentLength"] if "maxSegmentLength" in params and params["maxSegmentLength"] > 0 else 10
    retString = params["retString"] if "retString" in params else True

    fshapes = [ "M"+shape for shape in fromShape.split("M") if shape ]
    tshapes = [ "M"+shape for shape in toShape.split("M") if shape ]

    # if len(fshapes) != len(tshapes):
    fromRings, toRings = cut(fshapes, tshapes, maxSegmentLength)
    interpolators = [interpolateRing(fromRings[i], toRings[i], retString) for i in range(len(fromRings))]

    def _checkBeforeInterpolate(t):
        if t < 1e-4 and isinstance(fromShape, str):
            return fromShape
        elif 1 - t < 1e-4 and isinstance(toShape, str):
            return toShape
        return ''.join([interpolator(t) for interpolator in interpolators])
    
    return _checkBeforeInterpolate


    # fromRing = normalizeRing(fromShape, maxSegmentLength)
    # toRing = normalizeRing(toShape, maxSegmentLength)
    # interpolator = interpolateRing(fromRing, toRing, retString);

    # print(toShape)    
    # def _checkBeforeInterpolate(t):
    #     if t < 1e-4 and isinstance(fromShape, str):
    #         return fromShape
    #     elif 1 - t < 1e-4 and isinstance(toShape, str):
    #         return toShape
    #     return interpolator(t)
    
    # return _checkBeforeInterpolate


if __name__ == "__main__":
    path1 = "M59.00,103.14L59.00,41.00L136.00,41.00C207.50,41.00 213.00,41.12 213.00,42.68C213.00,46.41 204.51,69.12 199.55,78.66C192.33,92.56 186.38,101.27 176.61,112.21C149.21,142.94 110.65,161.75 69.25,164.58L59.00,165.29L59.00,103.14z"
    path2 = "M50,150 L150,50 L250,150 L150,250Z"

    interpolator = interpolate(path1, path2, {"maxSegmentLength":1})
    print(interpolator(0.5))
