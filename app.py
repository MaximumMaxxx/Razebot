from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/privacy")
def privacy():
    return render_template("imagine.html",route="Privacy Policy")

@app.route("/legal")
def legal():
    return render_template("imagine.html",route="Legal Anything")

@app.route("/about")
def about():
    return render_template("imagine.html",route="About Page")

@app.route("/support")
def support():
    return render_template("imagine.html",route="Support System")

@app.route("/contact")
def contact():
    return render_template("imagine.html",route="Contact Page")

@app.route("/dashboard")
def dashboard():
    return render_template("imagine.html",route="Dashboard")

if __name__ == '__main__':
    app.run(port="6969", host="localhost")