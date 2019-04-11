import os
from flask import Flask, flash, render_template, request, redirect, url_for
from flask import send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename, SharedDataMiddleware

# UPLOAD_FOLDER = 'static/uploads'
# ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__, static_url_path="/static")
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customers.sqlite3'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boots.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)
#customer table

# imagelist = ['static/uploads/BCARDFinal-02.png','static/uploads/Candy37X37test.jpg','static/uploads/Cone37X37test.jpg']
# print os.listdir('static/uploads')


class customers(db.Model):
   id = db.Column('customers_id', db.Integer, primary_key = True)
   name = db.Column(db.String(100))
   imgs = db.Column(db.String(50))
   size = db.Column(db.Numeric(5,1))
   width = db.Column(db.Numeric(5,2))
   length = db.Column(db.Numeric(5,2))

def __init__(self, name, imgs, size,width, length):
   self.name = name
   self.imgs = imgs
   self.size = size
   self.width = width
   self.length = length
#boots
class boots(db.Model):
   id = db.Column('boots_id', db.Integer, primary_key = True)
   name = db.Column(db.String(100))
   img = db.Column(db.String(50))
   sizes = db.Column(db.Numeric(5,1))
   width = db.Column(db.Numeric(5,2))
   length = db.Column(db.Numeric(5,2))

def __init__(self, name, img, sizes,width, length):
   self.name = name
   self.img = img
   self.sizes = sizes
   self.width = width
   self.length = length


# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

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
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
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
    return render_template('main.html', filenames=filenames)

# #image input
# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#
#
#
#
# @app.route('/', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         uploaded_files = request.files.getlist("file[]")
#         print(file.filename)
#         # if user does not select file, browser also
#         # submit a empty part without filename
#         filenames = []
#         for file in uploaded_files:
#             filename = secure_filename(file.filename)
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             filenames.append(filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             return redirect(url_for('upload_file',
#                                     filenames=filenames))
#     return render_template('main.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

# @app.route('/uploads/<filename>')
# def uploaded_file():
#     files = os.listdir('static/uploads')
#     return render_template('displayimg.html', files = )




if __name__ == "__main__":
    db.create_all()
    app.run()



    app = Flask(__name__)





