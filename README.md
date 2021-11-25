# FemInvest – Find the best companies to invest in

### Use filters to find the best Russian companies and see the number of women in their boards of directors!

* A web application using JavaScript, Python, and SQL added to an already existing WordPress website *

#### Video Demo:  <https://youtu.be/Cnk-v0C4m3I>

#### Web link: <https://bafr.fr/FinalProject>

#### Description:

This is basically a very useful app for investors. It questions a SQLite database for users and gives them all sorts of financial info about the company. It can also select for you only the companies that correspond to a certain filter criteria, like “Average income growth rate higher than 20%”. The database also contains information about the number of men and women in a company’s board of directors. All the text in the app is in Russian as I wanted to append it to my [WordPress website about feminism](https://bafr.fr), which I did: [https://bar.fr/FinalProject](https://bar.fr/FinalProject)

But you can translate it in English with your browser if necessary.

In the folder containing this text file you can find all the code as well as other files and directories that were created or modified by me in order for the app to work while attached to my website. Let me describe them one by one:

###### application.py

That’s basically the heart of the app – its Python code. It consists of 5 routes and a few additional functions.

**The root route** supports only GET method and doesn’t do much. It only queries a SQLite database (more about it below) for all the data in a “companies” table sorted in the way that companies with more women directors appear first. This data is assigned to a variable which is then returned by `render_template` together with the first html page, which I decided to call “project.html”.

** (“/company”) route** also supports only GET method and queries the database. This time it selects all info for a specific name in a “company_name” column from both “finance” and “companies” tables joined using a primary key “id”. The company name is received via `request.args.get`. The data received is stored in a variable called “data”. Then the function checks if “data” contains any value for a key “symbol” – this is where the company’s stock symbol should be. If the value is not none the program passes it to a function `Ticker` from an imported library `yfinance` which gets some info about a company from Yahoo Finance. After that the function returns “company.html” page with two variables: “data” for all the data received from the local database and “stock” which contains the stock’s current market price (part of the data received using `yfinance.Ticker()`).

**(“/filters”) route** `@app.route(“/filters”)` supports both GET and POST methods and calls two other functions. This one is pretty complex: it handles the requests from seven filters. Let me skip the first three filters for now and go to the last four which I defined in comments as P\S, Dividend, Equity to Assets ratio and Capitalisation filters.

These four are very similar. They first check if a request for this filter was made by the user and try to convert the value received via POST to a float. If the value cannot be converted to float, they return “filters.html” message with an Error message (displayed as alert by JavaScript). If the value is converted well, the program selects from the database “company_name” and a respective filter column (for example, “P/S, “ column) from companies where the filter column’s value is bigger (or in case of P/S smaller) than the value inputted by the user. It also makes sure to only look for the most recent values by ordering the column “Год” (ru. Year) in descending order and using LIMIT. After that the values selected are appender to a “company” list variable which was declared at the very beginning of the filters function.

Now let’s return to the first 3 filters. They are counting if a company parameter's growth rate is higher than the users input. These filters just call a function “growth” on the list of companies, appending the resulting list to the already-mentioned “company” variable.

Let’s see what the “growth” function does. It takes two arguments: user’s input (float) and the name of a filter column (string). It declares a list variable `c_list`, selects all companies from the database and runs a loop `for company in companies:`. For every company it selects values for the last 5 years (LTM year is not counted) from a column provided as an argument. The it append to the resulting list a float value 0.0 (zero) and calls another function – `average_growth`, comparing the result to the user’s input and appending it to `c_list` if it’s higher. The result is appended in the form of a dictionary with a key “ – тем роста” (ru. “growth rate”). There’s also another key-value pair in this dictionary - `’name’: company[“company_name”]`, which contains the name of the company this “growth rate” parameter belongs to.

The “average_growth” function takes 3 arguments: “data” list, column name and a span which will always be equal to 4 if we select data for 5 last years. But since I might change the number of years later and some companies have less than 5 years worth of data in the database, “span” value is calculated as `len(data) – 2` (remember, we appended 0.0 to the end of “data”, so we need to extract 2). If span is less than 1, the function just returns zero, as it’s impossible to calculate growth rate for just one year. The function is recursive. Its base condition is the following:

```
    if len(d) == 2:

        d.pop(0)

        d = (d[0] / span) * 100 - 100

        return d
```

That is to say, if there are only two elements left in the “data”/d list, delete the first one and divide the remaining by “span”, then multiply it by 100, extract 100 and return the final value.

Another part of the function uses recursion:

```
    else:

        d[-1] += float(d[1][col])/float(d[0][col])

        d.pop(0)

        return average_growth(d, col, span)
```

Remember “d[-1] is this zero float element we appended to “data” list in “growth” function.

The final part of the “filters” function allows to intersect the values in the lists stored in the “companies” list variable if more than one filter were used:

```
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
```

If “companies” remains empty it means that no filters were used and the function just redirects us to “/filters” route using GET as method. This returns filters.html template with a variable storing the names of all companies.

**(“/login”) route** is similar to the one provided in Problem Set 9 Finance and uses the same “login_required(f)” function. But instead of checking a database for a username and password it compares the input data to environment variables “admin” and “password”. This login function is only needed to restrict the access to “/update-db” route for everybody except an administrator, so there was no need for a database with multiple usernames.

**(“/update-db”) route** receives as input a company name, stock symbol, a number of men and women in the board of directors and a csv file containing financial info about this company (csv files in the form supported by my “upload” function were downloaded from a website [www.smart-lab.ru](https://smart-lab.ru).

The function first checks if a company already exists in the database. If the company is in there already, the function then might insert its stock symbol using UPDATE, in case such an input was provided. If there’s no such company, it will insert new rows.

```
check = db.execute(f'SELECT * FROM companies WHERE TRIM(company_name) LIKE TRIM(?)', name)

 if not check:

 # check if the company's data was already inserted once

 	db.execute("INSERT INTO companies (company_name, women, men, symbol) VALUES (?,?,?,?)", name, women, men, symbol)

elif symbol:

    db.execute(f'UPDATE companies SET symbol = ? WHERE TRIM(company_name) LIKE TRIM(?)', symbol, name)

# create a row for a new company
```

There was a difficult design choice I had to make while creating an “upload” function. In the csv tables I downloaded from *smart-lab.ru* the column names were years (aka 2016, 2017, 2018…). And the type of the data (income, Capitalisation, net income, P/S…) were all in the cells of a left column. However, different companies have different amount of year columns in their csv tables and I didn’t want my function to add new columns every time a new year value appears. I also didn’t want to limit the amount of years to insert in the database, since I want to be able to update the table in the following years adding new information. Thus, I decided to “rotate” the table and insert csv files in the database with data types’ names as columns. In this piece of code you can see how the function first inserts new rows for every new year in the csv table where the company_id corresponds to the company in question. Then it iterates over rows in DictReader and updates these newly-created rows with data from rows where the first value corresponds to one of my table’s existing columns (there might be data types specific to this company that shouldn’t be included):

```
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
```

###### passenger_wsgi.py

This file contains only one line:

```
from application import app as application
```

Apparently, this file is necessary for Passenger web application server to be able to run the code I wrote in application.py.

###### companies.db

A database I’ve already talked about. It has 2 tables The first is “companies”, which contains columns for company name, id (primary key), number of men and women directors and a stock symbol. The second is called “finance” and includes a company_id column (foreign key) and columns for different data types from csv files I used to create this database.

###### requirements.txt

There are not many libraries to “pip install”:

```
flask
flask_session
cs50
yfinance
```

The yfinance library I’ve mentioned before. It gives me access to actual stock prices from Yahoo Finance.

###### static/

Since I’m not much into graphic design, this folder contains only 2 things:

**Empty folder “files/”**

That’s where the csv files are uploaded. But after reading them the “upload” function will delete them so this folder remains empty.

**styles.css**

Nothing too elaborate here, but you might notice how I use fixed table layout and position “absolute” on the left column to make it unscrollable:

```
/* Make the table scrollable horizontally */

div {

    overflow-x: scroll;

    overflow-y: visible;

    padding: 0;

}

 /* Fixed table layout */

.scroll {

    background-color: transparent;

    margin-bottom: 1rem;

    table-layout: fixed;

}

table th,

table td {

    vertical-align: middle;

    width: 7em;

    height: 5em;

}

/* For the empty cell in thead above the fixed column */

.headrow {

    width: 10em;

}

/* Fix a column to its position on the screen */

.headcol {

    position: absolute;

    margin-bottom: 1rem;

    width: 10em;

}
```

And the size of the font adapts to a screen:

```
main

{

    /* Scroll horizontally as needed */

    overflow-x: auto;



    /* Center contents */

    text-align: center;



    font-size: calc(0.5em + 0.5vw);

}

/* Adjustable font size */

.header {

    font-size: calc(1.3em + 1.3vw);

}

.subhead {

    font-size: calc(1em + 1vw);

}
```

###### templates/

All in all, I’ve created 5 html pages:

**layout.html**

My layout is pretty simple. It’s pretty much a copy of Problem Set 9 Finance layout without some features like a nav bar. It defines language as Russian: `lang=”ru”`, adds Bootstrap and makes sure the page adapts to the screen size: `<meta name="viewport" content="initial-scale=1, width=device-width">`.

**project.html**

That’s my main page. I’ve decided not to call it index.html. No specific reason, I just wanted to call it “project”. This page receives all the data from the “companies” table in my database from the “/” route and displays in a table all companies in the database with a percentage and a number of women directors in them as well as a form that sends a company’s name to the “/company” route via GET:

```
    <div class="table-responsive">

    <table class="table table-hover">

        <thead>

            <tr>

                <th></th>

                <th colspan="2">Совет директоров</th>

                <th></th>

            </tr>

            <tr>

                <th>Название</th>

                <th>Процент женщин</th>

                <th>Число женщин</th>

                <th></th>

            </tr>

        </thead>

        <tbody>

            {% if not companies %}

            <tr>

                <td>--</td>

                <td>--</td>

            </tr>

            {% endif %}

            {% for company in companies %}

            <tr>

                <td id = name>{{company.company_name}}</td>

                <td>{{"{:.0%}".format(company.women/(company.women+company.men))}}</td>

                <td>{{company.women}}</td>

                <td>

                    <form id="company" action="{{ url_for('company') }}" method="get">

                        <input type="hidden" name="company" value="{{company.company_name}}">

                        <input type="submit" value="?">

                    </form>

                </td>

            </tr>

            {%endfor%}

        </tbody>

    </table>

    </div>
```

At the beginning of this page there’s also a form to access the “/filters” route. And a search bar. It takes text input, and JavaScript code notices this input the moment a keyboard key is pushed and hides or unhides the rows where a company name contains the inputted character or a string of characters:

```
<script>

    document.addEventListener('DOMContentLoaded', function() {

        var search = document.querySelector('input[type="text"]');

        search.addEventListener('keyup', function() {

            var cell = document.querySelectorAll("#name");

            for (c of cell)

            {

                if (c.innerHTML.indexOf(search.value) !== -1)

                {

                  c.parentNode.style.display = "table-row";

                }

                else

                {

                  c.parentNode.style.display = "none";

                }

            }

        });

    });

</script>
```

**company.html**

This page takes a variable containing all the data about a particular company from the “/company” route. It then displays most of the financial data in a table with the use of Jinja “if” conditions and “for” loops:

```
    <div class="table-responsive">

    <table class="table table-hover scroll">

        <thead>

            <tr>

                <th class="headrow"></th>

                {% for  d in data %}

                <th>{{d.Год}}</th>

                {%endfor%}

            </tr>

        </thead>

        <tbody>

            {% for key, value in data[0].items() %}

             {% if not key in ["company_id", "Год", "Дата отчета", "company_name", "id", "women", "men", "symbol"] %}

            <tr>

                <th class="table-danger headcol">{{key}}</td>

                {% for d in data %}

                <td>{{d[key]}}</td>

                {%endfor%}

            </tr>

             {% endif %}

            {%endfor%}

        </tbody>

    </div>
```

**filters.html**

Displays a form with 7 filters which sends a POST request to the “/filters” route. After the form it creates a table using all values in a variable it received from the route:

```
        <div class="table-responsive">

        <table class="table table-hover table-sm">

            <thead>

                {% if not companies %}

                <tr>

                    <th>Компании не найдены</td>

                </tr>

                {% else %}

                <tr>

                {% for key in companies[0] %}

                    {% if key == 'name' %}

                    <th>Компании</th>

                    {% else %}

                    <th>{{key}}</th>

                    {% endif %}

                {% endfor %}

                <th>Узнать больше:</th>

                </tr>

            </thead>

            <tbody>

                {% for company in companies %}

                <tr>

                    {% for value in company.values() %}

                    <td>{{value}}</td>

                    {% endfor %}

                    <td>

                        <form action="{{ url_for('company') }}" method="get">

                            <input type="hidden" name="company" value="{{company.name}}">

                            <input type="submit" value="?">

                        </form>

                    </td>

                </tr>

                {% endfor %}

                {% endif %}

            </tbody>

            </div>
```

You might have also noticed this piece of JavaScript code :

```
    if ('{{message}}')

    {

        alert('{{message}}');

    }
```

It can be found on several other html pages too. If something is wrong with the input, a router will return a variable “message” (which states where the error is) and then this message will be shown to a user as an alert. I think it’s a better way to create error messages, than redirecting users to another page every time.

**login.html**

It’s basically the same page as in Problem Set 9 Finance.

**upload.html**

Contains a form that takes various inputs and sends them to the “/update-db” route.

###### empty folders: company, filters, login, update-db

Without these folders, the server refuses to admit that the address exists and returns a 404 error. It was not the case in CS50 IDE, but the problem emerged when I was adding my web app to my WordPress website.