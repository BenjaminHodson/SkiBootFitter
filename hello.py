import os
from flask import Flask, flash, render_template, request, redirect, url_for
from flask import send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename, SharedDataMiddleware

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__, static_url_path="/static")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customers.sqlite3'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boots.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)
#customer table
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

#image input
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        print(file.filename)
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)



if __name__ == "__main__":
    db.create_all()
    app.run()



    app = Flask(__name__)





