from flask import Flask,render_template,request,redirect,url_for
from flask import flash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from flask import g 
import forms

from models import db
from models import Alumnos

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")


app=Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()





if __name__ == '__main__':
	csrf.init_app(app)
	db.init_app(app)
 
	with app.app_context():
		db.create_all()
	app.run()
 
 
 
 