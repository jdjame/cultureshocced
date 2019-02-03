from flask import Flask, render_template, request, session,g
from flask_mail import Mail,Message
from flaskext.mysql import MySQL
import os
app = Flask(__name__,static_url_path='/static')
app.secret_key=os.urandom(24)
mysql = MySQL()
app.config.update(dict(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'jkepaou8@gmail.com',
    MAIL_PASSWORD = 'mchacks2019',
))
mail=Mail(app)
attribute_list= [("name", "varchar(255)"), ("password", "varchar(255)"),("nationality","varchar(255)"), ("languages spoken","varchar(255)"), ("location","varchar(255)"), ("bio","varchar(255)"), ("interests","varchar(255)"), ("rating","int"),("friends","varchar(255)"),("email", "varchar(255)"),("username","varchar(255)")]
fields=["name","username","password","email","nationality","languages spoken", "location", "bio", "interests"]
fields=sorted(fields)
def conndb():
    app.config['MYSQL_DATABASE_USER'] = 'root'
    app.config['MYSQL_DATABASE_PASSWORD'] = 'UBUNTU'
    app.config['MYSQL_DATABASE_DB'] = 'cultureshock'
    app.config['MYSQL_DATABASE_HOST'] = 'localhost'
    mysql.init_app(app)
    conn = mysql.connect()
    cursor = conn.cursor()
    return (cursor,conn)



def create_table(connection,cursor,table_name,col_data_tuple):
    data_string=""
    #making a long string to be used in my query later
    col_data_tuple=list(col_data_tuple)
    for x in col_data_tuple:
        ret=0
        name,data=x
        if (col_data_tuple.index(x)<(len(col_data_tuple)-1)):
           data_string+= "`"+name+"`"+" "+data+","
        else:
           data_string+="`"+name+"`"+" "+data
    query= "create table "+ table_name+ " (`id` int not null auto_increment,"+ data_string+ ", primary key (id)"+ ")"
    try:
        cursor.execute(query)
        connection.commit()
    except:
        ret="error"
    connection.rollback()
    return ret
def close_db(conn):
        conn.close()
curs,conn= conndb()
create_table(conn,curs,"montreal_dataset",attribute_list)
close_db(conn)

#used to insert data into the sql db takes in a tuple of the column and the value you want to insert
def insert(connection, cursor, table_name, col_value_tuple):
    ret=0
    col_string= ""
    val_string= ""
    col_value_tuple=list(col_value_tuple)
    for x in col_value_tuple:
        col, val=x
        if (not val.isdigit()):
            val="\'"+val+"\'"
        if (col_value_tuple.index(x)<(len(col_value_tuple)-1)):
            col_string+="`"+col+"`"+", "
            val_string+=val+", "
        else:
            col_string+="`"+col+"`"
            val_string+=val
    query="insert into "+table_name+" ("+col_string+") values ("+val_string+")"
    try:
        cursor.execute(query)
        connection.commit()
    except:
        ret=query
        connection.rollback()
    return ret

def select_all(connection,cursor,table_name):
    query="select * from "+table_name
    result=0
    try:
        cursor.execute(query)
        result=cursor.fetchall()
        connection.commit()
    except:
        result=query
        connection.rollback()
    return result

#gets fields from a db and returns a list
def get_fields(connection,cursor,table_name):
    return_array=[]
    result=()
    query="desc "+table_name
    try:
        cursor.execute(query)
        result=cursor.fetchall()
        connection.commit()
    except :
        return query
        connection.rollback()
    for element in result:
        return_array.append(element[0])
    return return_array

def my_zip(field_list,row_tupples):
    return_dict={}
    for f in field_list:
        return_dict[f]=[row[field_list.index(f)] for row in row_tupples]
    return return_dict

def logcheck(unam,pword):
    ret=1
    curs,conn=conndb()
    query="select id from montreal_dataset where username='"+unam+"' and password='"+pword+"'";
    curs.execute(query)
    result=curs.fetchall()
    if (len(result)):
        ret=0
    close_db(conn)
    return ret

@app.route("/")
def test():
    return render_template("index.html")

@app.route("/signup",methods=['GET', 'POST'])
def su():
    if request.method=="GET":
        return render_template('profile.html')
    else:
        curs,conn= conndb()
        table= request.form['location'].lower() + "_dataset"
        info=[]

        pic=request.files["photo1"]
        outfile="static/images"+request.form["username"]+ "_profile_pic"
        pic.save(outfile)
        
        l=sorted(request.form.keys())
        for x in l:
            if(not x =="photo1"):
                info.append(request.form[x])
        ins=zip(fields, info)
        #print(request.form.keys)
        ret=insert(conn,curs,table,ins)
        print(ret)
        close_db(conn)
    return render_template("index.html")

@app.route("/timeline/<location>")
def timeline(location):
    if request.method=="Post":
        return render_template(" ns.html")
    curs,conn=conndb()
    table=location.lower()+ "_dataset"
    row_tupple=select_all(conn,curs,table)
    field_list=get_fields(conn,curs,table)
    lis=[]
    for row in row_tupple:
        dic={}
        for f in field_list:
            f2=f.replace(" ","_")
            dic[f2]=row[field_list.index(f)]
        lis.append(dic)
    close_db(conn)
    return render_template("timeline.html", profiles=lis )

@app.route("/login",methods=['GET', 'POST'])
def login():
    if request.method=='POST':
        if(not logcheck(request.form["username" ],request.form["password" ])):
            session['user']=request.form["username" ]
            return render_template('index.html')
    return render_template('login.html')
    
@app.route("/profile/<info>")
def profile(info):
    l=info.split('-')
    username=l[0]
    location=l[1]
    curs,conn=conndb()
    table=location.lower()+ "_dataset"

    field_list=get_fields(conn,curs,table)
    query="select * from "+ table+" where username='"+ username+ "'";
    curs.execute(query)
    result=curs.fetchall()
    dic={}
    for row in result:
        for f in field_list:
            f2=f.replace(" ","_")
            dic[f2]=row[field_list.index(f)]
    return render_template("user.html",p=dic)

@app.route('/protected',methods=['GET', 'POST'])
def protected():
    if g.user:
        return render_template('protected.html')
    return render_template('login.html')
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

@app.route('/friend/<info>',methods=['GET', 'POST'])
def friend(info):
    if g.user:
        l=info.split('-')
        their_username=l[0]
        location=l[1]
        my_username=session['user']
        table=location.lower()+ "_dataset"
        curs,conn=conndb()
        query="select friends from "+table +" where username='"+my_username+"'"
        curs.execute(query)
        friends=curs.fetchall()[0][0]
        friends=friends + "-"+ their_username
        query="update montreal_dataset set friends = '"+friends+"' where username='"+my_username+"'"
        curs.execute(query)
        conn.commit()
        result=curs.fetchall()
        return render_template("index.html")
    return render_template("login.html")
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

@app.route('/message/<info>',methods=['GET', 'POST'])
def message(info):
    if g.user:
        l=info.split('-')
        their_email=l[0]
        location=l[1]
        my_username=session['user']
        table=location.lower()+ "_dataset"
        curs,conn=conndb()
        query="select email from "+table +" where username='"+my_username+"'"
        curs.execute(query)
        friends=curs.fetchall()[0][0]
        text= "You've got a message from "+my_username+ " via CultureShoCCed! "
        msg = Message(text,sender="jkepaou8@gmail.com",recipients=[their_email])
        msg.body=request.form["message"]
        print(mail.send(msg))
        return render_template("index.html")
    return render_template("login.html")
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']