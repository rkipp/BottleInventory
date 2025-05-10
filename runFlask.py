from flask import Flask, render_template, request, redirect, url_for
from invManagement import Inventory
import brewfather

app = Flask(__name__)
inv = Inventory()  # Load inventory from CSV

@app.route("/view")
def view():
    inventory = inv.inventory  # Get current inventory
    return render_template("viewOnly.html", inventory=inventory)

@app.route("/group")
def view_grouped():
    return render_template("grouped.html", inventory=inv.group_inventory())

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        print(request.form)
        action = request.form["action"]  # Check which button was clicked

        if action == "update":
            brewfather.update_batches()
            return redirect(url_for("index"))  # Refresh the page
        
        size = int(request.form["bottle_size"])
        quantity = int(request.form["quantity"])
        filled_with = request.form["filled_with"]
        if filled_with == "__custom__":
            filled_with = request.form["filled_with_custom"]

        if action == "add":
            inv.add_bottles(size, quantity, filled_with)
        elif action == "fill":
            inv.fill_bottles(size, quantity, filled_with)
        elif action == "empty":
            inv.empty_bottles(size, quantity, filled_with)
        elif action == "remove":
            inv.remove_bottles(size, quantity, filled_with)        

        return redirect(url_for("index"))  # Refresh the page

    inventory = inv.group_inventory()  # Get current inventory
    batches = brewfather.get_batches()  # Get batches from Brewfather
    fermenting = brewfather.get_whats_fermenting()  # Get fermenting batches
    if batches.height == 0:
        batches = {"name": ["No batches found"]}
    if fermenting.height == 0:
        fermenting = {"name": []}
    return render_template("index.html", inventory=inventory, batches=batches["name"].to_list(), fermenting=fermenting["name"].to_list())

if __name__ == "__main__":
    brewfather.update_batches()
    app.run(debug=False)