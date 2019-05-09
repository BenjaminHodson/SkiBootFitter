from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import sqlalchemy
import os
from flask import Flask, render_template, request, redirect, url_for
from flask import send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename, SharedDataMiddleware
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
import time


global dimArray
dimArray = []

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__, static_url_path="/static")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boots.sqlite3'
app.config['SECRET_KEY'] = "random string"


def getSizeOfObject(filePath, f):
    def midpoint(ptA, ptB):
        return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)
    # load the image, convert it to grayscale, and blur it slightly
    image = cv2.imread(filePath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)

    # perform edge detection, then perform a dilation + erosion to
    # close gaps in between object edges
    edged = cv2.Canny(gray, 50, 100)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)

    # find contours in the edge map
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    # sort the contours from left-to-right and initialize the
    # 'pixels per metric' calibration variable
    (cnts, _) = contours.sort_contours(cnts)
    pixelsPerMetric = None

    num = 0
    # loop over the contours individually
    for c in cnts:
        # if the contour is not sufficiently large, ignore it
        if cv2.contourArea(c) < 100:
            continue

        # compute the rotated bounding box of the contour
        orig = image.copy()
        box = cv2.minAreaRect(c)
        box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
        box = np.array(box, dtype="int")

        # order the points in the contour such that they appear
        # in top-left, top-right, bottom-right, and bottom-left
        # order, then draw the outline of the rotated bounding
        # box
        box = perspective.order_points(box)
        cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)

        # loop over the original points and draw them
        for (x, y) in box:
            cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)

        # unpack the ordered bounding box, then compute the midpoint
        # between the top-left and top-right coordinates, followed by
        # the midpoint between bottom-left and bottom-right coordinates
        (tl, tr, br, bl) = box
        (tltrX, tltrY) = midpoint(tl, tr)
        (blbrX, blbrY) = midpoint(bl, br)

        # compute the midpoint between the top-left and top-right points,
        # followed by the midpoint between the top-righ and bottom-right
        (tlblX, tlblY) = midpoint(tl, bl)
        (trbrX, trbrY) = midpoint(tr, br)

        # draw the midpoints on the image
        cv2.circle(orig, (int(tltrX), int(tltrY)), 5, (255, 0, 0), -1)
        cv2.circle(orig, (int(blbrX), int(blbrY)), 5, (255, 0, 0), -1)
        cv2.circle(orig, (int(tlblX), int(tlblY)), 5, (255, 0, 0), -1)
        cv2.circle(orig, (int(trbrX), int(trbrY)), 5, (255, 0, 0), -1)

        # draw lines between the midpoints
        cv2.line(orig, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),
                 (255, 0, 255), 2)
        cv2.line(orig, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),
                 (255, 0, 255), 2)

        # compute the Euclidean distance between the midpoints
        dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
        dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

        # if the pixels per metric has not been initialized, then
        # compute it as the ratio of pixels to supplied metric
        # (in this case, inches)
        if pixelsPerMetric is None:
            pixelsPerMetric = dB / 0.955

        # compute the size of the object
        dimA = dA / pixelsPerMetric
        dimB = dB / pixelsPerMetric

        if (dimA + dimB) < 4:
            continue

        # draw the object sizes on the image
        cv2.putText(orig, "{:.1f}in".format(dimA),
                    (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (0, 0, 0), 2)
        cv2.putText(orig, "{:.1f}in".format(dimB),
                    (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (0, 0, 0), 2)

        cv2.imwrite('static/outimages/savedImage_' +
                    str(f) + '_' + str(num) + '.png', orig)
        global savedDimA
        savedDimA = dimA * 2.54
        savedDimB = dimB * 2.54

        dimArray.append(savedDimA)
        num += 1

        return(savedDimA, savedDimB)
#########################################################################################


# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(
    ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# For a given file, return whether it's an allowed type or not


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('main.html')


# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
    #print (uploaded_files)
    filenames = []
    for file in uploaded_files:
        # Check if the file is one of the allowed types/extensions
        if file and allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Save the filename into a list, we'll use it later
            filenames.append(filename)
            # Redirect the user to the uploaded_file route, which
            # will basicaly show on the browser the uploaded file
    # Load an html page with a link to each uploaded file

    uploadedfiles = os.listdir('static/uploads')

    length = len(filenames)
    for f in range(length):
        #    print('uploads/' + filenames[f])
        getSizeOfObject('static/uploads/' + filenames[f], f)
    # getSizeOfObject('static/uploads/foot1.jpg')

    return render_template('displayimg.html', filenames=filenames)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#######################################################################################
@app.route('/measure', methods=['GET', 'POST'])
def measure():
    # Get the name of the uploaded files
    measurements = os.listdir('static/outimages')
    print(measurements)
    length = len(measurements)
    isLength = 0
    for m in range(length):
        print("isLength: " + str(isLength))
        if(isLength < length):
            print('static/outimages/' + measurements[m])
            getSizeOfObject('static/outimages/' + measurements[m], m)
            isLength += 1
    bootArray = [boot1, boot2, boot3]
    lenArray = len(bootArray)
    for b in range(lenArray):
        if(bootArray[b].size < (dimArray[0]) and bootArray[b].size > (dimArray[0] - 1)):
            print('Comparison: ', bootArray[b].name)
            boot = bootArray[b].bootIMG
            bootSize = bootArray[b].size
            bootName = bootArray[b].name
            print(boot)

    print('THIS: ', boot1.size)
    return render_template('displaymeasurments.html', measurements=measurements, boot=boot, bootSize=bootSize, bootName=bootName)


class Boots:
    def __init__(self, name, id, size, bootIMG):
        self.name = name
        self.id = id
        self.size = size
        self.bootIMG = bootIMG


global boot1, boot2, boot3
boot1 = Boots('Dalbelo Lupo TI', 1, 27.5, 'boot1.png')
boot2 = Boots('boot2', 2, 26.5, 'boot1.png')
boot3 = Boots('boot3', 3, 29.5, 'urlforimg')
#print (savedDimA)


if __name__ == "__main__":
    app.run(debug=True)
    app = Flask(__name__)
