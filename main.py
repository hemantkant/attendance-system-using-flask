from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
import cv2,os
import numpy as np
from PIL import Image, ImageTk
from datetime import date
import time

app = Flask(__name__)
app.secret_key = "hemant"
my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db="admin")
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


def TrackImages(sub,total):
    rn = session['rn']
    branch = session['branch']
    my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
    mycursor = my_db.cursor()

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
        sql = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '"+branch+"' AND TABLE_NAME = '"+sub+"' AND COLUMN_NAME = '" + d4 + "'"
        res = mycursor.execute(sql)
        print("hye")
        if res:
            print("exist")
            mycursor.execute("select "+d4+" from "+sub+" where rn= "+str(Id)+"")
            sql = mycursor.fetchone()
            if sql:
                mycursor.execute("update "+sub+" set total= "+str(total[0])+", "+d4+" ='present' where rn= "+str(Id)+"")
            else:
                mycursor.execute("update " + sub + " set total= " + str((total[0]+ 1)) + ", " + d4 + " ='present' where rn= " + str(Id) + "")
            my_db.commit()
        else:
            print("not exist")
            mycursor.execute("alter table "+sub+" add column " + d4 + " varchar(20)")
            mycursor.execute("update "+sub+" set total= "+str((total[0]+1))+", "+d4+" ='present' where rn= "+str(Id)+"")
            my_db.commit()

    else:
        pass
    cam.release()
    cv2.destroyAllWindows()

#######################################################################################################################




def camera(rn,name,branch,sem):
    my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
    mycursor = my_db.cursor()
    semn = "sem"+str(sem)
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
    sql = "insert into "+semn+"(rn,name,branch,sem) values(%s,%s,%s,%s)"
    val = (rn, name, branch, sem)
    mycursor.execute(sql, val)
    mycursor.execute("select sub from subject where sem= "+sem+"")
    result = mycursor.fetchall()
    for i in result:
        total = 0
        val = (rn, name, branch, sem, total)
        sql = "insert into "+i[0]+" (rn,name,branch,sem,total) values(%s,%s,%s,%s,%s)"
        mycursor.execute(sql, val)
    my_db.commit()


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
        rn = int(request.form["rn"])
        sem = request.form["sem"]
        branch = request.form["branch"]
        my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
        mycursor = my_db.cursor()
        semn = "sem" + str(sem)
        mycursor.execute("select rn from "+semn+" where rn= "+str(rn)+"")
        result = mycursor.fetchone()
        if rn == result[0]:
            session['rn'] = request.form["rn"]
            session['sem'] = request.form["sem"]
            session['branch'] = request.form["branch"]
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

    if 'rn' in session:
        heading = { 0: 'mobile', 1: 'mail', 2: 'address'}
        rn = session['rn']
        sem = session['sem']
        branch = session['branch']
        my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
        mycursor = my_db.cursor()
        semn = "sem" + str(sem)
        mycursor.execute("select mobile,mail,address  from "+semn+" where rn="+rn+"")
        result = mycursor.fetchone()
        print(result)
        return render_template('profile.html', rn=rn, result=result, heading=heading)
    else:
        return render_template('/')

#######################################################################################################################
#update profile
@app.route('/updateprofile', methods=["POST", "GET"])
def updateprofile():
    if request.method == "POST":
        rn = session['rn']
        sem = session['sem']
        semn = "sem" + str(sem)
        mobile = request.form['mobile']
        mail = request.form['mail']
        address = request.form['address']
        branch = session['branch']
        my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
        mycursor = my_db.cursor()
        sql = "update "+semn+" set mobile="+mobile+", mail='"+mail+"', address='"+address+"' where rn="+rn+""

        mycursor.execute(sql)
        my_db.commit()
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('student'))

######################################################################################################################
# mark attendance
@app.route('/studentsub')
def studentsub():
    if 'rn' in session:
        rn = session['rn']
        sem = session['sem']
        branch = session['branch']
        my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
        mycursor = my_db.cursor()
        mycursor.execute("select sub from subject where sem= "+sem+"")
        result = mycursor.fetchall()
        print(result)
        return render_template('studentsub.html',result=result)
    else:
        return redirect(url_for('index'))

######################################################################################################################
# mark attendance
@app.route('/markattendance/<sub>')
def markattendance(sub):
    if 'rn' in session:
        branch = session['branch']
        sem = session['sem']
        my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
        mycursor = my_db.cursor()
        mycursor.execute("select total from "+sub+" where sem= "+sem+"")
        total = mycursor.fetchone()
        print(total)
        TrainImages()
        TrackImages(sub,total)
        return redirect(url_for('student'))
    else:
        return redirect(url_for('index'))

######################################################################################################################
# mark attendance
@app.route('/checksub')
def checksub():
    if 'rn' in session:
        rn = session['rn']
        sem = session['sem']
        branch = session['branch']
        my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
        mycursor = my_db.cursor()
        mycursor.execute("select sub from subject where sem= "+sem+"")
        result = mycursor.fetchall()
        print(result)
        return render_template('checksub.html',result=result)
    else:
        return redirect(url_for('index'))
######################################################################################################################
# check attendance
@app.route('/checkattendance/<sub>')
def checkattendance(sub):
    if 'rn' in session:
        rn = session['rn']
        branch = session['branch']
        sem = session['sem']
        my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
        mycursor = my_db.cursor()
        mycursor.execute("select COLUMN_NAME from INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '"+sub+"'")
        result = mycursor.fetchall()
        print(result)
        col = []
        for i in result:
            col.append(i[0])
        print(col)
        size = len(col)
        mycursor.execute("select * from "+sub+" where rn= "+rn+"")
        values = mycursor.fetchall()
        print(values)
        return render_template('checkattendance.html', values=values, col=col, size=size)
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
        mycursor.execute("select * from admin where admin= '"+uname+"' and password= '"+pas+"'")
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
        if 'uname' in session:
            return render_template('teacher.html')
        else:
            return redirect(url_for('index'))

#########################################################################
@app.route('/sem/<branch>')
def sem(branch):
    session['branch'] = branch
    return render_template('sem.html')

#########################################################################

@app.route('/teacheroption/<sem>')
def teacheroption(sem):
    session['sem'] = sem
    return render_template('teacheroption.html')

#########################################################################
#register
@app.route('/register')
def register():
    return render_template('register.html')
#########################################################################
#register a student
@app.route('/register1', methods=["POST", "GET"])
def register1():
    if request.method == "POST":
        branch = session['branch']
        sem = session['sem']
        rn = request.form["rn"]
        name = request.form["name"]
        camera(rn,name,branch,sem)
        return render_template("register.html")
    else:
        return render_template("register.html")

########################################################################### mark attendance
@app.route('/teachersub')
def teachersub():
    if 'uname' in session:
        sem = session['sem']
        branch = session['branch']
        my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
        mycursor = my_db.cursor()
        mycursor.execute("select sub from subject where sem= "+sem+"")
        result = mycursor.fetchall()
        print(result)
        return render_template('teachersub.html',result=result)
    else:
        return redirect(url_for('index'))

######################################################################################################################
# check attendance
@app.route('/roll/<sub>')
def roll(sub):
    if 'uname' in session:
        branch = session['branch']
        sem = session['sem']
        session['sub'] = sub
        return render_template('roll.html')
    else:
        return redirect(url_for('index'))

######################################################################################################################
# check attendance
@app.route('/teacherattendance', methods=["POST", "GET"])
def teacherattendance():
    if request.method == "POST":
        rn = request.form["rn"]
        branch = session['branch']
        sem = session['sem']
        sub = session['sub']
        my_db = pymysql.connect(host="127.0.0.1", user="root", password="Password@4", port=3306, db=branch)
        mycursor = my_db.cursor()
        mycursor.execute("select COLUMN_NAME from INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '"+sub+"'")
        result = mycursor.fetchall()
        print(result)
        col = []
        for i in result:
            col.append(i[0])
        print(col)
        size = len(col)
        mycursor.execute("select * from "+sub+" where rn= "+rn+"")
        values = mycursor.fetchall()
        print(values)
        return render_template('teacherattendance.html', values=values, col=col, size=size)
    else:
        return redirect(url_for('index'))
#######################################################################################################################

if __name__ == "__main__":
    app.run(debug=True)