from flask import (
    Flask,
    render_template,
    request,
    url_for,
    redirect,
    session,
    flash
)

import requests
import base64

from mongoengine import connect
from models.clients import Clients
from models.logs import Logs
from models.rfid_data import RFID
from models.payments import Payments
from flask_bcrypt import check_password_hash, generate_password_hash

import math
from pymongo import MongoClient
import pwds
from flask_mail import Mail, Message
from datetime import datetime, date, timedelta

from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# mongodb://localhost:27017/IOT
# Connection to the database
try:
    connect(host="mongodb://localhost:27017/IOT")
    print("Connection with success")

except Exception as ex:
    print(ex)

try:
    con = MongoClient('mongodb://localhost:27017/')
    print("pymongo connected")
except Exception as ex:
    print(ex)

# the secret_key is essential in session connection
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
app.secret_key = "testing"
app.config['SECRET_KEY'] = 'testing'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'Your Gmail Address'
app.config['MAIL_PASSWORD'] = 'Your Gmail Password'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


usertes= con.IOT.clients.find()

tags=con.IOT.r_f_i_d



@app.route("/", methods=["POST", "GET"])
@app.route("/index", methods=["POST", "GET"])
def index():
    message = ""
    # Admin Handling
    if "id" in session:
        c = Clients.objects.get(id=session["id"])
        if c.is_admin:
            return redirect(url_for("admin"))
        else:
            return redirect(url_for("user", id=session["id"]))
        return redirect(url_for("user", id=session["id"]))

    if request.method == "POST":
        em = request.form.get("email")
        passw = request.form.get("password")

        # check if email exists in database
        cl = Clients.objects(email=em).first()
        if cl:
            if check_password_hash(cl["password"], passw):
                session["id"] = str(cl.pk)
                if cl.is_admin:
                    return redirect(url_for("admin"))
                else:
                    return redirect(url_for("user", id=session["id"]))
            else:
                return render_template("index.html", message="Incorrect Password")
        else:
            return render_template("index.html", message="Email does not exist")
    else:
        return render_template("index.html")


@app.route("/user/<id>", methods=["POST", "GET"])
def user(id):
    c = Clients.objects.get(id=session["id"])
    if c.is_admin:
        return redirect(url_for("admin"))
    if session["id"] == id:
        try:
            lots = 5
            hourly_rate = 50
            c = Clients.objects.get(id=id)
            l = Logs.objects(client=id)
            p = Payments.objects(client=id)
            r=RFID.objects.get(client=id)
            used_lots = RFID.objects(is_used=True).count()
            parking_times = Logs.objects(client=id).count()

            av_lots = lots - used_lots

            # TOP_UP Button

            if request.method == "POST":
                amount = request.form.get("amount")
                amount = int(amount)
                while amount > 0 and c.money_debt > 0:
                    amount -= 1
                    c.money_debt -= 1
                    c.total_money += 1
                if c.money_debt == 0:
                    pf = Payments.objects(client=c.id).order_by("-id").first()
                    pf.is_payment_successful = True
                    r.tag_suspended=False
                    r.save()
                    pf.save()

                c.balance += amount
                c.save()

                return redirect(url_for("user", id=c.id))

            if request.method == "GET":
                # **********Handling Weeks***********
                today = date.today()
                weekday = today.weekday()
                # lower bound
                mon = today - timedelta(days=weekday)
                # upper bound
                sun = today + timedelta(days=(7 - weekday))

                print(mon)
                print(sun)

                # **********Handling Months***********

                days_per_month = {
                    1: 31,
                    2: 29,
                    3: 31,
                    4: 30,
                    5: 31,
                    6: 30,
                    7: 31,
                    8: 31,
                    9: 30,
                    10: 31,
                    11: 30,
                    12: 31,
                }
                # lower bound
                first = today.replace(day=1)
                # upper bound
                try:
                    last = today.replace(day=days_per_month[today.month])
                except ValueError:
                    if today.month == 2:  # Not a leap year
                        last = today.replace(day=28)

                # **********Handling Years***********

                # lower bound
                janfirst = today.replace(month=1, day=1)
                # upper bound
                declast = today.replace(month=12, day=31)

                # Getting the number of parking_times
                # By Current Week
                nlog = l(entry_date__gte=mon)
                parking_times_week = nlog(entry_date__lte=sun).count()

                # By Current Month
                nlog = l(entry_date__gt=first)
                parking_times_month = nlog(entry_date__lt=last).count()

                # By Current Year
                nlog = l(entry_date__gt=janfirst)
                parking_times_year = nlog(entry_date__lt=declast).count()

                # Getting The Total_Money_Spent
                # By Current Week
                total_amount_week = 0
                nlog = l(entry_date__gt=mon)
                logs = nlog(entry_date__lt=sun)
                for i in logs:
                    pay = Payments.objects.get(log=i.id)
                    if pay.is_payment_successful == True:
                        total_amount_week += pay.payment_amount
                # By Current Month
                # By Current Month
                total_amount_month = 0
                nlog = l(entry_date__gt=first)
                logs = nlog(entry_date__lt=last)
                for i in logs:
                    pay = Payments.objects.get(log=i.id)
                    if pay.is_payment_successful == True:
                        total_amount_month += pay.payment_amount
                # By Current Year
                total_amount_year = 0
                nlog = l(entry_date__gt=janfirst)
                logs = nlog(entry_date__lt=declast)
                for i in logs:
                    pay = Payments.objects.get(log=i.id)
                    if pay.is_payment_successful == True:
                        total_amount_year += pay.payment_amount

                # Calculate to pay amount
                # paid_amount = hourly_rate * time_of_parking_in_hour

                total_money = 0
                money_debt = 0
                for log in l:
                    en = log.entry_date
                    ex = log.exit_date
                    log.entry_date = log.entry_date.strftime("%d-%m-%Y %H:%M:%S")
                    log.exit_date = log.exit_date.strftime("%d-%m-%Y %H:%M:%S")

                    # Getting client information

                fn = c.first_name
                ln = c.last_name
                em = c.email
                balance = c.balance
                picture = c.picture_url
                client_info = zip(l, p)
        except Exception as e:
            print(e)
    else:
        return redirect(url_for("err"))

    return render_template(
        "user.html",
        fn=fn,
        ln=ln,
        em=em,
        client_info=client_info,
        c=c,
        payments=p,
        user=user,
        picture=picture,
        parking_times=parking_times,
        parking_times_week=parking_times_week,
        parking_times_month=parking_times_month,
        parking_times_year=parking_times_year,
        balance=balance,
        total_amount_week=total_amount_week,
        total_amount_month=total_amount_month,
        total_amount_year=total_amount_year,
        av_lots=av_lots
    )


#
# TODO : Edit profile
# TODO : Handle banned users admin user
# TODO : Handle admin and user dashboard


@app.route("/admin/signup", methods=['POST', 'GET'])
def signup():
    c = Clients.objects.get(id=session["id"])
    if not c.is_admin:
        return redirect(url_for("user", id=session["id"]))
    usable_tags=tags.find({"is_reserved": False})
    usable_tags_l=list(usable_tags)
    utag=[]
    for i in usable_tags_l:
        uti=str(i["tag_identifier"]).replace(" ", "-")
        # utag.append(i["tag_identifier"])
        utag.append(uti)
        print(uti)
    session["utag"]=utag
    if request.method == 'POST':
        users = con.IOT.clients
        
        signup_user = users.find({'email': request.form['email']})    #used to be find_one
        listensignupuser=list(signup_user)
        if len(listensignupuser)!=0:
            flash(request.form['email'] + ' email already exists')
            return redirect(url_for('signup'))

        ln=request.form['lastname']
        fn=request.form['firstname']
        em=request.form['email']
        bl=request.form['credit']
        pw=request.form['password']
        t=str(request.form['Tags']).replace("-", " ")
        c=Clients(first_name=fn,
        last_name=ln,
        email=em,
        balance=bl,
        password=pw,
        tag=t)
        c.save()
        
        clientfortag=users.find_one({'email': em})
        cft=clientfortag["_id"]
        tags.update_one({"tag_identifier": t}, {"$set": {"is_reserved": True}})
        tags.update_one({"tag_identifier": t}, {"$set": {"client": cft}})
        return redirect(url_for('admin'))

    return render_template('signup.html', utag=session["utag"])


@app.route("/admin")
def admin():
    c = Clients.objects.get(id=session["id"])
    if not c.is_admin:
        return redirect(url_for("user", id=session["id"]))
    return render_template('admin.html')

logs = []


@app.route('/admin/logs')
def logs():
    c = Clients.objects.get(id=session["id"])
    if not c.is_admin:
        return redirect(url_for("user", id=session["id"]))
    lolo=con.IOT.logs
    # Look up related documents in the 'comments' collection:
    stage_getclients = {
    "$lookup": {
            "from": "clients", 
            "localField": "client", 
            "foreignField": "_id", 
            "as": "clientfortag",
        }
    }
    pipeline = [
        stage_getclients
    ]
    logssss = lolo.aggregate(pipeline)
    alllogs = []
    hourly_rate = 50
    for logg in logssss:
        entryd = logg["entry_date"]  # .strftime("%d-%m-%Y %H:%M:%S")
        exitd = logg["exit_date"]  # .strftime("%d-%m-%Y %H:%M:%S")
        diff = exitd - entryd
        diff_in_hours = diff.total_seconds() / 3600
        paid = round(diff_in_hours * hourly_rate)
    
        onelog={
            "username": logg["clientfortag"][0]["first_name"]+ " "+logg["clientfortag"][0]["last_name"],
            "email": logg["clientfortag"][0]["email"],
            "used_tag": logg["clientfortag"][0]["tag"],
            "entry_date": entryd,
            "exit_date": exitd,
            "paid_amount": paid
        }
        alllogs.append(onelog)

    return render_template('logs.html', alllogs=alllogs)


@app.route('/admin/reportage', methods=['POST', 'GET'])
def reportage():
    c = Clients.objects.get(id=session["id"])
    if not c.is_admin:
        return redirect(url_for("user", id=session["id"]))
    # firstdate="2022/01/01 00:00:00.000000"
    # lastdate="2099/12/31 00:00:00.000000"
    if request.method == 'POST':
        # signup_user = users.find({'username': request.form['username']})    #used to be find_one

        firstdate = request.form['FDATE']
        lastdate = request.form['LDATE']
        if (firstdate != ""):
            firstdate = firstdate.replace('-', '/') + " 00:00:00.000000"

        else:
            firstdate = "2022/01/01 00:00:00.000000"

        if (lastdate != ""):
            lastdate = lastdate.replace('-', '/') + " 00:00:00.000000"
        else:
            lastdate = "2099/12/31 00:00:00.000000"

        fdate = datetime.strptime(firstdate, '%Y/%m/%d %H:%M:%S.%f')
        ldate = datetime.strptime(lastdate, '%Y/%m/%d %H:%M:%S.%f')
        session['fdate'] = fdate
        session['ldate'] = ldate

        return redirect(url_for('.reportage'))

    if 'fdate' in session:
        fdate = session['fdate']
    else:
        fdate = datetime.strptime("2022/01/01 00:00:00.000000", '%Y/%m/%d %H:%M:%S.%f')
    if 'ldate' in session:	
        ldate=session['ldate']	
    else:	
        ldate=datetime.strptime("2099/12/31 00:00:00.000000", '%Y/%m/%d %H:%M:%S.%f')

    lolo=con.IOT.logs
  
    # Look up related documents in the 'comments' collection:
    stage23 = {
        "$match": {
            "entry_date": {"$gt": fdate},
            "exit_date": {"$lt": ldate}
        }
    }
    stage_getclients = {
        "$lookup": {
            "from": "clients", 
            "localField": "client", 
            "foreignField": "_id", 
            "as": "clientfortag",
        }
    }
    pipeline = [
        stage_getclients, stage23
    ]
    logssss = lolo.aggregate(pipeline)

   
    alllogs = []
    hourly_rate = 50
    for logg in logssss:
        entryd = logg["entry_date"]  # .strftime("%d-%m-%Y %H:%M:%S")
        exitd = logg["exit_date"]  # .strftime("%d-%m-%Y %H:%M:%S")
        diff = exitd - entryd
        diff_in_hours = diff.total_seconds() / 3600
        paid = round(diff_in_hours * hourly_rate)

        onelog={
            "username": logg["clientfortag"][0]["first_name"]+ " "+logg["clientfortag"][0]["last_name"],
            "email": logg["clientfortag"][0]["email"],
            "used_tag":logg["clientfortag"][0]["tag"],      #this could be tag_identifier instead
            "entry_date":entryd,
            "exit_date":exitd,
            "paid_amount":int(paid)           
        }
        alllogs.append(onelog)
    taux_occup = []
    taux_hours = []
    totalpaid = 0
    for i in alllogs:
        entryd = i["entry_date"]  # .strftime("%d-%m-%Y %H:%M:%S")
        exitd = i["exit_date"]  # .strftime("%d-%m-%Y %H:%M:%S")
        diff = exitd - entryd
        diff_in_hours = diff.total_seconds() / 3600
        diff_in_hours = int(math.ceil(diff_in_hours))
        taux_occup.append(diff_in_hours)
        taux_hours.append(entryd.hour)
        paid = diff_in_hours * hourly_rate

        totalpaid=totalpaid+paid
    
    sethours=set(taux_hours)
    setoccup=set(taux_occup)
    # print("POSTED")
    # print(sethours)
    # print(setoccup)
    # print(taux_hours)
    # print(taux_occup)

    stathours = []
    for i in sethours:
        c = taux_hours.count(i)
        n_hour = {
            "hour": i,
            "repetition": c
        }
        stathours.append(n_hour)

    statocc = []
    for i in setoccup:
        c = taux_occup.count(i)
        n_occup = {
            "hours": i,
            "repetition": c
        }
        statocc.append(n_occup)

    bestusers=[]
    allusers=con.IOT.clients.find()
    for i in allusers:
        amount_by_user = 0
        for j in alllogs:
            if(i["email"]==j["email"]):
                amount_by_user=amount_by_user+int(j["paid_amount"])
        gooduser={
            "username": i["email"],
            "paid_amount":amount_by_user
        }
        bestusers.append(gooduser)
    pipe23 = [
        stage23
    ]

    datinglogs = lolo.aggregate(pipe23)
    ourlist = list(datinglogs)

    return render_template('reportage.html', totalpaid=totalpaid, stathours=stathours, statocc=statocc,
                           bestusers=bestusers)


@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "id" in session:
        session.pop("id", None)
        return redirect(url_for("index"))
    else:
        return redirect(url_for("index"))


@app.route("/404")
def err():
    return render_template("404.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# Handle RFID Tags from http request
# 56-E5-1B-9E    allowed
# FA-92-5D-59  suspended
@app.route("/entry", methods=["POST"])
def entry():
    # Getting RFID Tag from hardware
    data = request.json["rfid"]
    try:
        lots = 5
        r = RFID.objects.get(tag_identifier=data)
        cl = Clients.objects.get(id=r.client.id)
        used_lots = RFID.objects(is_used=True).count()
        av_lots = lots - used_lots
        fn = cl.first_name

        if r.tag_suspended == False and r.is_used == False and av_lots > 0:
            # update tag status
            r.is_used = True
            # Add log

            l = Logs(client=r.client.id,
                     used_tag=r.id)
            # commit to database
            l.save()
            p = Payments(client=r.client.id,
                         log=l.id)

            r.save()
            p.save()
            # Sending firstname of client
            return fn
        #  Tag suspended
        elif r.tag_suspended == True:
            return "Tag Suspended"
        #     Tag Already Used
        elif r.is_used == True:
            return "Tag Already Used"
        elif av_lots == 0:
            return "We are Full"

    #      Client doesn't exist

    except RFID.DoesNotExist:
        return "Tag Not Found"
    except AttributeError:
        return "Tag Not Found"


@app.route("/exit", methods=["POST"])
def exit():
    data = request.json["rfid"]
    hourly_rate = 50
    try:
        r = RFID.objects.get(tag_identifier=data)
        l = Logs.objects(used_tag=r.id).order_by("-id").first()
        p = Payments.objects(client=l.client.id).order_by("-id").first()
        c = Clients.objects.get(id=l.client.id)

        # Last Conditions
        if  not r.tag_suspended and r.is_used:


            

            ex = datetime.now()
            diff = ex - l.entry_date
            diff_in_hours = diff.total_seconds() / 3600
            to_pay = round(diff_in_hours * hourly_rate)
            p.payment_amount = to_pay

            # Check the current balance

            if c.balance > to_pay:
                c.balance -= to_pay
                p.is_payment_successful = True
                c.total_money += to_pay
            else:
                while c.balance > 0:
                    c.balance -= 1
                    to_pay -= 1
                    c.total_money += 1
                c.money_debt += to_pay
                r.tag_suspended = True
                p.is_payment_successful = False

            # Update Payments document
            p.log = l.id
            p.save()
            # Update Logs document
            l.exit_date = ex

            r.is_used = False
            l.save()
            c.save()
            r.save()
            return "Thank you"
            
        else :
            return "DENIED"
    except RFID.DoesNotExist:
        return "DENIED"
    except Payments.DoesNotExist:
        return "DENIED"
    except Logs.DoesNotExist:
        return "DENIED"
    except Clients.DoesNotExist:
        return "DENIED"
    except AttributeError:
        return "DENIED"

@app.route("/email", methods=["POST", "GET"])
def sendemail():
    data = request.json["rfid"]
    try:
        r = RFID.objects.get(tag_identifier=data)
        c = Clients.objects.get(id=r.client.id)
        if c.balance < 100:
            gmail_user = 'Your Gmail Account'
            subject = 'Keep your balance loaded to prevent service interruptions 💸'
            body = 'Hello ' + c.first_name + ' ' + c.last_name + ', from IParking! 👋\nYour balance is getting low, you wouldn\'t be able to park your car long with it.\nWe suggest that you load it again.'
            msg = Message(subject, sender=gmail_user, recipients=[c.email])
            msg.body = body
            mail.send(msg)
        return "True"
    except RFID.DoesNotExist:
        return "DENIED"
    except Payments.DoesNotExist:
        return "DENIED"
    except Logs.DoesNotExist:
        return "DENIED"
    except Clients.DoesNotExist:
        return "DENIED"
    except AttributeError:
        return "DENIED" 
@app.route("/profile/<id>", methods=["POST", "GET"])
def profile(id):
    message = []
    if session["id"] == id:
        try:

            c = Clients.objects.get(id=id)
            fn = c.first_name
            ln = c.last_name
            em = c.email
            picture = c.picture_url

            # forms handling
            if request.method == "POST":
                if request.files["image"]:
                    pic = request.files["image"]
                    url = "https://api.imgbb.com/1/upload"
                    payload = {
                        "key": IMGBB_API_KEY,
                        "image": base64.b64encode(pic.read()),
                    }
                    response = requests.post(url, payload).json()
                    c.picture_url = response["data"]["url"]
                    c.save()
                email = request.form.get("email")
                fnn = request.form.get("firstname")
                lnn = request.form.get("lastname")
                passw = request.form.get("password")

                # check between the old values and the new ones

                # email
                if em != email:
                    # check if email exists in database
                    cl = Clients.objects(email=email).first()
                    if cl:
                        message.append("Email Exist !!!")
                        return render_template(
                            "profile.html", picture=picture, fn=fn, ln=ln, em=em, message=message
                        )
                    else:
                        c.email = email
                        c.save()
                        message.append("Email Updated Successfully")

                # firstname
                if fn != fnn:
                    c.first_name = fnn
                    c.save()
                    message.append("Firstname Updated Successfully")

                # lastname
                if ln != lnn:
                    c.last_name = lnn
                    c.save()
                    message.append("Lastname Updated Successfully")

                # Password
                if passw:
                    c.password = generate_password_hash(passw).decode("utf-8")
                    c.save()
                    message.append("Password Updated Successfully")

            else:
                return render_template(
                    "profile.html", picture=picture, fn=fn, ln=ln, em=em, message=message
                )

        except Exception as ex:
            print(ex)
    else:
        return redirect(url_for("err"))

    return render_template(
        "profile.html", picture=picture, fn=fnn, ln=lnn, em=email, message=message
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
