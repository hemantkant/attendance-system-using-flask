from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
import cv2,os
import numpy as np
from PIL import Image, ImageTk
from datetime import date
import time

app = Flask(__name__)
app.secret_key = "hemant"

my_db = pymysql.connect(host = "127.0.0.1",user = "root",password="Password@4",port=3306, db = "pythonface")
mycursor = my_db.cursor()

########################################################################################################################

def TrainImages():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    harcascadePath = "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(harcascadePath)
    faces, Id = getImagesAndLabels("TrainingImage")
    recognizer.train(faces, np.array(Id))
    recognizer.save("Trainner.yml")


def getImagesAndLabels(path):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]

    faces = []
    Ids = []

    for imagePath in imagePaths:
        pilImage = Image.open(imagePath).convert('L')

        imageNp = np.array(pilImage, 'uint8')

        Id = int(os.path.split(imagePath)[-1].split(".")[1])

        faces.append(imageNp)
        Ids.append(Id)
    return faces, Ids


def TrackImages():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("Trainner.yml")
    harcascadePath = "haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(harcascadePath);
    cam = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    while True:
        ret, im = cam.read()
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.2, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(im, (x, y), (x + w, y + h), (250, 0, 0), 2)
            Id, conf = recognizer.predict(gray[y:y + h, x:x + w])
            if (conf < 50):
                tt = str(Id)
            else:
                Id = 'Unknown'
                tt = str(Id)
            """if(conf > 75):
                noOfFile=len(os.listdir("ImagesUnknown"))+1
                cv2.imwrite("ImagesUnknown\Image"+str(noOfFile) + ".jpg", im[y:y+h,x:x+w])"""

            cv2.putText(im, str(tt), (x, y + h), font, 1, (255, 255, 255), 2)
        cv2.imshow('im', im)
        if (cv2.waitKey(1) == ord('s')):
            break
    if Id != "Unknown":
        today = date.today()
        d4 = today.strftime("%b_%d_%Y")
        sql = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'pythonface' AND TABLE_NAME = 'iot' AND COLUMN_NAME = '" + d4 + "'"
        res = mycursor.execute(sql)
        if res:
            mycursor.execute("update iot set " + d4 + "='present' where id= "+str(Id)+"")
            my_db.commit()
        else:
            mycursor.execute(
                "alter table iot add column " + d4 + " varchar(20) AFTER id")
            mycursor.execute("update iot set " + d4 + "='present' where id= "+str(Id)+"")
            my_db.commit()

    else:
        pass
    cam.release()
    cv2.destroyAllWindows()

#######################################################################################################################


def table():
    today = date.today()
    d4 = today.strftime("%b_%d_%Y")
    mycursor.execute("create table " + d4 + " select * from student")
    # mycursor.execute("insert into "+d4+"(id,name) select id,name from student")
    mycursor.execute(
        "alter table " + d4 + " add column attendance varchar(50) after name, add column dt DATETIME after name")
    my_db.commit()


def camera(rn,name):
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
            cv2.imwrite("TrainingImage\ " + name + "." + rn + '.' + str(sampleNum) + ".jpg", gray[y:y + h, x:x + w])

            cv2.imshow('frame', img)

        if cv2.waitKey(300) & 0xFF == ord('q'):
            break

        elif sampleNum > 14:
            break
    cam.release()
    cv2.destroyAllWindows()
    sql = "insert into student(id,name) values(%s,%s)"
    val = (rn, name)
    mycursor.execute(sql, val)
    my_db.commit()

def loggedIn(un,pas):
    tup = (un, pas)
    mycursor.execute("select * from admin")
    result = mycursor.fetchall()
    if tup in result:
        return tup
    else:
        return False
#######################################################################
# main function
@app.route('/')
def index():
    return render_template('index.html')
#########################################################################
#student function
@app.route('/student', methods=["POST", "GET"])
def student():
    if request.method == "POST":
        print("post")
        rn = int(request.form["rn"])
        name = request.form["name"]
        tup = (rn, name)
        print(tup)
        mycursor.execute("select * from student where id= "+str(rn)+" and name= '"+name+"'")
        result = mycursor.fetchone()
        print(result)
        if tup == result:
            session['rn'] = request.form["rn"]
            session['name'] = request.form["name"]
            return render_template('student.html')
        else:
            return redirect(url_for('index'))
    else:
        print("get")
        if 'rn' in session:
            return render_template('student.html')
        else:
            return redirect(url_for('index'))

#######################################################################################################################
#profile function
@app.route('/profile')
def profile():
    heading = {0:'id', 1:'name', 2:'sem', 3:'mobile_no'}
    if 'rn' in session:
        rn = session['rn']
        mycursor.execute("select * from profile where id="+rn+"")
        result = mycursor.fetchone()
        print(result)
        return render_template('profile.html',result=result, heading=heading)
    else:
        return render_template('/')

#######################################################################################################################
#update profile
@app.route('/updateprofile', methods=["POST", "GET"])
def updateprofile():
    if request.method == "POST":

        id = request.form['id']
        name = request.form['name']
        sem = request.form['sem']
        mobile_no = request.form['mobile_no']
        sql = "update profile set id="+id+", name='"+name+"', sem="+sem+", mobile_no="+mobile_no+" where id="+id+""

        mycursor.execute(sql)
        my_db.commit()
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('student'))

######################################################################################################################
# mark attendance
@app.route('/markattendance')
def markattendance():
    if 'rn' in session:
        rn = session['rn']
        TrainImages()
        TrackImages()
        return redirect(url_for('student'))
    else:
        return redirect(url_for('index'))

#########################################################################
#teacher function
@app.route('/teacher', methods=["POST", "GET"])
def teacher():
    if request.method == "POST":
        print("post")
        uname = request.form["uname"]
        pas = request.form["pas"]
        tup = (uname, pas)
        print(tup)
        mycursor.execute("select * from admin where username= '"+uname+"' and password= '"+pas+"'")
        result = mycursor.fetchone()
        print(result)
        if tup == result:
            session['uname'] = uname
            session['pas'] = pas
            return render_template('teacher.html')
        else:
            return redirect(url_for('index'))
    else:
        print("get")
        return redirect(url_for('index'))

#########################################################################
@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/login')
def login():
    return render_template('login.html')







#######################################################################################################################

@app.route('/table')
def table1():
    table()
    return render_template('student.html')





@app.route('/admin', methods=["POST", "GET"])
def admin():
    if request.method == "POST":
        rn = request.form["rn"]
        name = request.form["name"]
        camera(rn,name)
        return render_template("login.html")
    else:
        return render_template("login.html")


@app.route('/camera')
def camera1():
    #camera()
    return render_template('attendance.html')

@app.route('/takeatt')
def takeatt():
    TrainImages()
    TrackImages()
    return render_template('student.html')



if __name__ == "__main__":
    app.run(debug=True)