from flask import Flask, render_template
from web_scrape import webscrape

app = Flask(__name__)


@app.route("/")
def index():
	webscrape()
	return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)