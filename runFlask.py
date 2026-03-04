from flask import Flask, render_template, request, redirect, url_for
from invManagement import Inventory
import brewfather

app = Flask(__name__)
inv = Inventory()  # Load inventory from CSV

@app.route("/edit", methods=["GET", "POST"])
def edit_inventory():
    inv = Inventory()
    if request.method == "POST":
        sizes = request.form.getlist("BottleSize")
        quantities = request.form.getlist("Quantity")
        filleds = request.form.getlist("FilledWith")

        new_data = []
        for size, qty, filled in zip(sizes, quantities, filleds):
            new_data.append({
                "BottleSize": size,
                "Quantity": qty,
                "FilledWith": filled if filled else "Empty"
            })

        inv.replace_inventory(new_data)
        return redirect(url_for("edit_inventory"))

    batches = brewfather.get_batches()["name"].to_list()
    return render_template("edit.html", inventory=inv.get_inventory(), batches=batches)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        print(request.form)
        action = request.form["action"]

        if action == "update":
            archived_names = brewfather.update_batches()
            inv.auto_empty_archived(archived_names)
            return redirect(url_for("index"))

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

        return redirect(url_for("index"))

    inventory = inv.group_inventory()
    batches = brewfather.get_batches()["name"].to_list()
    fermenting = brewfather.get_whats_fermenting()["name"].to_list()
    if len(fermenting) == 0:
        fermenting = False
    return render_template("index.html", inventory=inventory, batches=batches, fermenting=fermenting, empty_capacity=inv.calculate_empty_capacity())

if __name__ == "__main__":
    brewfather.update_batches()
    app.run(debug=True, port=8085)