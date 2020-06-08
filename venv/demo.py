from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import cv2,os

app = Flask(__name__)
app.consfig['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///admin.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db  = SQLAlchemy(app)

class admin(db.Model):
    _id = db.column("id", db.Integer, primary_key=True)
    name = db.column(db.String(100))
    password = db.column(db.String(100))

    def __init__(self, name, password):
        self.name = name
        self.password = password

def camera():
    Id = "1"
    name = "hemant"
    width, height = 800, 600
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    harcascadePath = "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(harcascadePath)
    sampleNum = 0
    while (True):
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

            sampleNum = sampleNum + 1
            cv2.imwrite("TrainingImage\ " + name + "." + Id + '.' + str(sampleNum) + ".jpg", gray[y:y + h, x:x + w])

            cv2.imshow('frame', img)

        if cv2.waitKey(300) & 0xFF == ord('q'):
            break

        elif sampleNum > 14:
            break
    cam.release()
    cv2.destroyAllWindows()

def loggedIn(id,pas):
    pass

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/student')
def student():
    return render_template('student.html')

@app.route('/teacher')
def teacher():
    return render_template('teacher.html')

@app.route('/admin', methods=["POST", "GET"])
def admin():
    if request.method == "POST":
        un = request.form["un"]
        pas = request.form["pass"]
        res = loggedIn(un,pas)
        if res:
            return render_template('attendance.html')
        else:
            return render_template("login.html")


def teacher():
    return render_template('teacher.html')

@app.route('/camera')
def camera1():
    camera()
    return render_template('attendance.html')

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)