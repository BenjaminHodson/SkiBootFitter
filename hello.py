from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import sqlalchemy
import os
from flask import Flask, flash, render_template, request, redirect, url_for
from flask import send_from_directory
from werkzeug.utils import secure_filename
#from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename, SharedDataMiddleware
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
# from flask-images import resized_img_src


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__, static_url_path="/static")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boots.sqlite3'
app.config['SECRET_KEY'] = "random string"
#images = Images(app)

#db = SQLAlchemy(app)
# customer table

#DATABASE###################################################################################
# engine = create_engine('sqlite:///:memory:', echo=True)
# Base = declarative_base()


# class Boots(Base):
#     __tablename__ = 'boots'
#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     length = Column(Integer)
#     width = Column(Integer)

#     def __repr__(self):
#         return "<Boots(name='%s', length='%d', width='%d')>" % (
#             self.name, self.length, self.width)


# Boots.__table__
# Table('Boots', MetaData(bind=None),
# Column('id', Integer(), table= < boots > , primary_key=True, nullable=False),
# Column('name', String(), table= < boots > ),
# Column('length', Integer(), table= < boots > ),
# Column('width', Integer(), table= < boots > ), schema=None)

# Base.metadata.create_all(engine)
#n opencv for foot mesurment ###############################################################


def getSizeOfObject(filePath, f):
    def midpoint(ptA, ptB):
        return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

    # construct the argument parse and parse the arguments
    # ap = argparse.ArgumentParser()
    # ap.add_argument("-i", "--image", required=True,
    #                 help="path to the input image")
    # ap.add_argument("-w", "--width", type=float, required=True,
    #                 help="width of the left-most object in the image (in inches)")
    # args = vars(ap.parse_args())

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

        # cropping image
        # crop_img = orig[ytR:ybR, xtL:xtR]

        # saving image

        cv2.imwrite('static/outimages/savedImage_' +
                    str(f) + '_' + str(num) + '.png', orig)
        savedDimA = dimA * 2.54
        savedDimB = dimB * 2.54
        print('MondopointA value: ' + str(savedDimA) +
              ' MondopointB value: ' + str(savedDimB))

        num += 1

        # cv2.imshow("Image",crop_img)

        # show the output image
        #cv2.imshow("Image", orig)
        # cv2.waitKey(0)


# getSizeOfObject('images/IMG_0429.jpg')


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
    # getSizeOfObject(filenames[0])
    #
   # print (uploadedfiles)

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

# @app.route('/measure',Methods=["POST","GET"])
# def measure():


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @app.route('/size', methods=[ 'POST'])
# def size():
    # call getSizeOfObject
    # return redirect( to display new cv procssed images )
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

    return render_template('displaymeasurments.html', measurements=measurements)


if __name__ == "__main__":
   # db.create_all()
   # getSizeOfObject('images/IMG_0429.jpg')
    app.run(debug=True)

    #app = Flask(__name__)
