import numpy as np
import scipy.optimize
from sys import exit
from pprint import pprint

def iou(a,b):
    if a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]:
        return 0

    aW = a[2]-a[0]+1
    aH = a[3]-a[1]+1
    bW = b[2]-b[0]+1
    bH = b[3]-b[1]+1

    aArea = aW*aH
    bArea = bW*bH

    intersection = [
        max(a[0],b[0]),
        max(a[1],b[1]),
        min(a[2],b[2]),
        min(a[3],b[3])
    ]

    intersectionW = max(0,intersection[2]-intersection[0]+1)
    intersectionH = max(0,intersection[3]-intersection[1]+1)
    intersectionArea = intersectionW*intersectionH

    unionArea = aArea+bArea-intersectionArea

    return intersectionArea/unionArea if unionArea !=0 else 0

def readList(listFile,count,detection=False):
    testList = []
    with open(listFile, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.rstrip()
        if line == '' or line[0] == '#':
            continue

        line = line.replace(' ','')
        lineSplit = line.split('\t')

        if detection:
            boxes_ = [ float(lineSplit[i]) for i in range(1,len(lineSplit)) ]
            boxes_ = [ int(v) if (i+1)%5!=0 else v for i,v in enumerate(boxes_) ]
            boxes = np.reshape( boxes_, (-1,5) )
            scores = boxes[:,4].tolist()
            boxes = boxes[:,:4].tolist()
            testList.append({
                "image_path":lineSplit[0],
                "boxes":boxes,
                "scores":scores
            })
        else:
            boxes_ = [ float(lineSplit[i]) for i in range(count,len(lineSplit)) ]
            boxes_ = [ int(v) if (i+1)%5!=0 else v for i,v in enumerate(boxes_) ]
            boxes = np.reshape( boxes_, (-1,5) )
            labels = boxes[:,4].tolist()
            boxes = boxes[:,:4].tolist()
            testList.append({
                "image_path":lineSplit[count-1],
                "boxes":boxes,
                "labels":labels
            })

    testList.sort(key=lambda x: x["image_path"])

    return testList

def maxPair(scores, boxes, labels, boxesGt, threshold, minHeight=None, maxHeight=None, mask=None):
    detections = []

    if len(scores) == 0:
        return detections

    cost = np.zeros( shape=(len(boxes),len(boxesGt)), dtype=np.float64 )

    for i,ei in enumerate(boxes):
        for j,ej in enumerate(boxesGt):
            iouVal = iou(ei,ej)
            cost[i][j] = 1 - iouVal

    rows, cols = scipy.optimize.linear_sum_assignment(cost)

    selectedIndicesI = rows.tolist()
    selectedIndicesJ = cols.tolist()

    for i in range(len(scores)):
        if i in selectedIndicesI:
            j = selectedIndicesI.index(i)
            if mask and labels[selectedIndicesJ[j]] == 0:
                continue
            if 1 - cost[i][selectedIndicesJ[j]] > threshold:
                if minHeight is not None or maxHeight is not None:
                    selectedIndex = selectedIndicesJ[j]
                    selectedGt = boxesGt[selectedIndex]
                    selectedHeight = selectedGt[3] - selectedGt[1] + 1
                    if (minHeight is not None and selectedHeight < minHeight) or \
                        (maxHeight is not None and selectedHeight > maxHeight):
                        continue
                truePositive = True
            else:
                truePositive = False

        else:
            if minHeight is not None or maxHeight is not None:
                selectedIndex = i
                selected = boxes[selectedIndex]
                selectedHeight = selected[3] - selected[1] + 1
                if (minHeight is not None and selectedHeight < minHeight) or \
                    (maxHeight is not None and selectedHeight > maxHeight):
                    continue
            truePositive = False

        if truePositive:
            detections.append([scores[i],1])
        else:
            detections.append([scores[i],0])

    return detections

def heightFilter(l_,minHeight,maxHeight,labels=None):
    l = l_[:]

    if labels is not None:
        l = [ e for i,e in enumerate(l) if labels[i] != 0 ]

    if minHeight is not None:
        l = [ e for e in l if e[3]-e[1]+1 >= minHeight ]
    if maxHeight is not None:
        l = [ e for e in l if e[3]-e[1]+1 <= maxHeight ]

    return l
