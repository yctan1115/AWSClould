from crypt import methods
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *
import re

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')

@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')

@app.route("/getallemp", methods=['GET', 'POST'])
def GetAllEmp():
    employees = []
    try:
        cursorObject = db_conn.cursor()                                     
        sqlQuery = "select * from employee"
        cursorObject.execute(sqlQuery)
        employees = cursorObject.fetchall()

    except Exception as e:
        return str(e)
    finally:
        cursorObject.close()
        

    return render_template('ViewAllEmp.html', employees=employees)

@app.route("/getemp", methods=['GET'])
def GetEmp():
    id = request.args.get("id")

    if id:
        try:
            cursorObject = db_conn.cursor()                                     
            sqlQuery = "select * from employee where emp_id = " + id
            cursorObject.execute(sqlQuery)
            employee = cursorObject.fetchone()

        except Exception as e:
            return str(e)
        finally:
            cursorObject.close()
    else:
        GetAllEmp()

    return render_template('GetEmpOutput.html', employee=employee)


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        print("Data inserted in MySQL RDS... uploading image to S3...")
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file" + "-" + emp_image_file.filename
        s3 = boto3.resource('s3')

        s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
        bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
        s3_location = (bucket_location['LocationConstraint'])

        if s3_location is None:
            s3_location = ''
        else:
            s3_location = '-' + s3_location

        object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
            s3_location,
            custombucket,
            emp_image_file_name_in_s3)

        try:
            cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location, object_url))
            db_conn.commit()
            emp_name = "" + first_name + " " + last_name

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True) 
