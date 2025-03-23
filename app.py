from flask import Flask, render_template, request, redirect, url_for
from invManagement import Inventory

app = Flask(__name__)
inv = Inventory()  # Load inventory from CSV

@app.route("/view")
def view():
    inventory = inv.inventory  # Get current inventory
    return render_template("viewOnly.html", inventory=inventory)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        size = int(request.form["bottle_size"])
        quantity = int(request.form["quantity"])
        filled_with = request.form["filled_with"] or None
        action = request.form["action"]  # Check which button was clicked

        if action == "add":
            inv.add_bottles(size, quantity, filled_with)
        if action == "fill":
            inv.fill_bottles(size, quantity, filled_with)
        if action == "empty":
            inv.empty_bottles(size, quantity, filled_with)
        elif action == "remove":
            inv.remove_bottles(size, quantity, filled_with)

        return redirect(url_for("index"))  # Refresh the page

    inventory = inv.inventory  # Get current inventory
    return render_template("index.html", inventory=inventory)

if __name__ == "__main__":
    app.run(debug=True)