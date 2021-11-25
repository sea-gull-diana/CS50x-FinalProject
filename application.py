import os
import csv
import yfinance

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_session import Session
from os.path import join, dirname, realpath
from functools import wraps
from tempfile import mkdtemp

# Configure application
app = Flask(__name__)

app.config["APPLICATION_ROOT"] = "/FinalProject"

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["DEBUG"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///companies.db")

UPLOAD_FOLDER = 'static/files'
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    companies = db.execute("SELECT * FROM companies ORDER BY women DESC")
    return render_template("project.html", companies=companies)


@app.route("/company")
def company():
    company = request.args.get("company")
    data = db.execute("SELECT * FROM finance JOIN companies ON id = company_id WHERE company_name = ?", company)
    if not data[0]['symbol']:
        return render_template("company.html", data=data)
    else:
        stock = yfinance.Ticker(data[0]['symbol'])
        return render_template("company.html", data=data, stock=stock.info['regularMarketPrice'])
    


@app.route("/filters", methods=['POST', 'GET'])
def filters():
    if request.method == 'POST':
        companies = []
        # Income growth filter
        inc = request.form.get("income")
        if inc:
            if not inc.isdigit():
                return render_template("filters.html", message="Параметр 'темп прироста выручки' задан некорректно.")
            else:
                companies.append(growth(inc, "Выручка, млрд руб"))

        # Net income growth filter
        net = request.form.get("net")
        if net:
            if not net.isdigit():
                return render_template("filters.html", message="Параметр 'темп роста чистой прибыли' задан некорректно.")
            else:
                companies.append(growth(net, "Чистая прибыль, млрд руб"))

        # Assets growth filter
        assets = request.form.get("assets")
        if assets:
            if not assets.isdigit():
                return render_template("filters.html", message="Параметр 'темп роста активов' задан некорректно.")
            else:
                companies.append(growth(assets, "Активы, млрд руб"))

        # P/S filter
        ps = request.form.get("ps")
        if ps:
            try:
                ps = float(ps) 
            except ValueError:
                return render_template("filters.html", message="Параметр P/S задан некорректно.")
            data = db.execute(f'SELECT company_name AS name, "P/S, " AS "P/S:" FROM finance JOIN companies ON id = company_id WHERE "P/S, " < ? AND Год != "LTM" AND Год IN (SELECT DISTINCT Год FROM finance ORDER BY Год DESC LIMIT 2)', ps)
            companies.append(data)

        # Dividend filter
        div = request.form.get("div")
        if div:
            try:
                div = float(div)
            except ValueError:
                return render_template("filters.html", message="Параметр Див доходность задан некорректно.")
            data = db.execute(f'SELECT company_name AS name, "Див доход, ао, %" AS "Див. доходность:" FROM finance JOIN companies ON id = company_id WHERE CAST(TRIM("Див доход, ао, %","%") AS REAL) > ? AND Год != "LTM" AND Год IN (SELECT DISTINCT Год FROM finance ORDER BY Год DESC LIMIT 2)', div)
            companies.append(data)

        # Equity to assets ratio filter
        equ = request.form.get("equ")
        if equ:
            try:
                equ = float(equ)
            except ValueError:
                return render_template("filters.html", message="Параметр Капитализация задан некорректно.")
            data = db.execute(f'SELECT company_name AS name, CAST(ROUND("Чистые активы, млрд руб"/"Активы, млрд руб"*100) AS INT) + "%" AS "Доля собственного капитала, %:" FROM finance JOIN companies ON id = company_id WHERE "Чистые активы, млрд руб"/"Активы, млрд руб"*100 > ? AND Год != "LTM" AND Год IN (SELECT DISTINCT Год FROM finance ORDER BY Год DESC LIMIT 2)', equ)
            companies.append(data)

        # Capitalisation filter
        cap = request.form.get("cap")
        if cap:
            try:
                cap = float(cap)
            except ValueError:
                return render_template("filters.html", message="Параметр Капитализация задан некорректно.")
            data = db.execute(f'SELECT company_name AS name, "Капитализация, млрд руб" AS "Капитализация, млрд руб:" FROM finance JOIN companies ON id = company_id WHERE "Капитализация, млрд руб" > ? AND Год != "LTM" AND Год IN (SELECT DISTINCT Год FROM finance ORDER BY Год DESC LIMIT 2)', cap)
            companies.append(data)

        # Intersect the results of all the filters used
        if len(companies) == 0:
            # if no filters were used, return all companies' names
            return redirect(url_for('filters'))
        # if more than one filter was used
        elif len(companies) > 1:
            # append company names of every filter result in the lists inside a variable "list"
            list = [[] for i in range (len(companies))]
            for i in range(len(companies)):
                for company in companies[i]:
                    list[i].append(company['name'])
                # intersect lists with company names
                list[0] = set(list[0]).intersection(set(list[i]))

            # create a list "names" and store the resulting company names in separate dicts inside it
            names = []
            for name in list[0]:
                names.append({'name': name})
            # Iterate over dicts in "companies" lists and in names checking if the values of 'name' are same
            for i in range(len(companies)):
                for company in companies[i]:
                    for name in names:
                        if company['name'] == name['name']:
                            # add data in "company" dict to "name" dict with the same 'name' value
                            name.update(company)
            return render_template("filters.html", companies=names)
        return render_template("filters.html", companies=companies[0])
    else:
        comp = db.execute("SELECT company_name AS name FROM companies")
        return render_template("filters.html", companies = comp)
        
        
def growth(p, col):
    c_list = []
    companies = db.execute("SELECT id, company_name FROM companies")
    for company in companies:
        data = db.execute(f'SELECT "{col}" FROM finance WHERE company_id = ? AND "{col}" != "" AND Год != "LTM" AND Год IN (SELECT DISTINCT Год FROM finance ORDER BY Год DESC LIMIT 6)', company["id"])
        data.append(0.0)
        av = average_growth(data, col, len(data) - 2)
        if av > float(p):
            c_list.append({'name': company["company_name"], col[: -10] + " - темп роста:": f"{round(av)}%"})
    return(c_list)


def average_growth(d, col, span):
    # check if there are at list 2 numbers in d
    if span < 1:
        return 0
    if len(d) == 2:
        d.pop(0)
        d = (d[0] / span) * 100 - 100
        return d
    else:
        d[-1] += float(d[1][col])/float(d[0][col])
        d.pop(0)
        return average_growth(d, col, span)


def login_required(f):
    # Decorate routes to require login.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":

        # Ensure username was submitted
        if request.form.get("username") == os.getenv("admin") and request.form.get("password") == os.getenv("password"):
            session["user_id"] = "tsetserau"

        # Redirect user to home page
        return redirect(url_for('upload'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/update-db", methods=['POST', 'GET'])
@login_required
def upload():
    if request.method == 'POST':
        name = request.form.get("name")
        if not name:
            return render_template("upload.html", message="Ошибка. Требуется ввести имя компании!")
        check = db.execute(f'SELECT * FROM companies WHERE TRIM(company_name) LIKE TRIM(?)', name)
        symbol = request.form.get("symbol")
        if not symbol and not check:
            return render_template("upload.html", message="Ошибка. Требуется ввести символ компании!")
        if symbol:
            try:
                yfinance.Ticker(symbol).info['regularMarketPrice']
            except:
                return render_template("upload.html", message="Ошибка. Несуществующий символ компании!")
        women = request.form.get("women")
        men = request.form.get("men")
        if not check and (not women.isdigit() or not men.isdigit() or int(women) < 0 or int(men) < 0):
            return render_template("upload.html", message="Ошибка. Требуется указать количество мужчин и женщин!")
        file = request.files['file']
        if not file.filename and not check:
            return render_template("upload.html", message="Ошибка. Вставьте csv файл!")
        elif file.filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
              # set the file path
            file.save(file_path)
              # save the file
        if not check:
            # check if the company's data was already inserted once
            db.execute("INSERT INTO companies (company_name, women, men, symbol) VALUES (?,?,?,?)", name, women, men, symbol)
        elif symbol:
            db.execute(f'UPDATE companies SET symbol = ? WHERE TRIM(company_name) LIKE TRIM(?)', symbol, name)
             # create a row for a new company
        if file.filename:
            id = db.execute('SELECT id FROM companies WHERE TRIM(company_name) LIKE TRIM(?)', name)[0]["id"]
                # get the company's unique id
            with open(f"{file_path}", encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=";")
                years = next(reader)
                for year in years:
                    # Iterate over column names
                    if year and not db.execute("SELECT * FROM finance WHERE Год = ? AND company_id = ?", year, id):
                        db.execute("INSERT INTO finance (company_id, Год, ?) VALUES (?, ?, ?)", years[""], id, year, years[f"{year}"])
                            # create rows for every year in the csv file unless such a year already exists for this company
                line = db.execute("SELECT * FROM finance WHERE rowid = 1")[0]
                columns = line.keys()

                for row in reader:
                    for year in years:
                        # Iterate over column names
                        if year and row[""] in columns:
                            db.execute("UPDATE finance SET ? = REPLACE(?, ',', '.') WHERE company_id = ? AND Год = ?", row[""], row[f"{year}"], id, year)
            os.remove(file_path)
        return render_template("upload.html", message="Готово!")
    else:
        return render_template("upload.html")
        
        
if __name__ == '__main__':
    app.run(ssl_context='adhoc')
        