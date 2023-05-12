import quart
import quart_trio

app = quart_trio.QuartTrio(__name__, template_folder="frontend")


@app.route("/")
async def index():
    return await quart.render_template("index.html")


if __name__ == "__main__":
    app.run()
