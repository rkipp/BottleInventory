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
    batches_df = brewfather.get_batches()
    batches = batches_df["name"].to_list()
    batch_info = {
        row["name"]: {
            "abv": row["measuredAbv"],
            "style": row["style"],
            "color": brewfather.srm_to_hex(row.get("estimatedColor"))
        }
        for row in batches_df.to_dicts()
    }

    fermenting_df = brewfather.get_whats_fermenting()
    fermenting_list = [
        {"name": row["name"], "color": brewfather.srm_to_hex(row.get("estimatedColor"))}
        for row in fermenting_df.to_dicts()
    ]
    fermenting = fermenting_list if fermenting_list else False

    all_inventory = inv.get_inventory()
    # All distinct bottle sizes owned
    all_bottle_sizes = sorted(set(item["BottleSize"] for item in all_inventory if item["BottleSize"] != 320), reverse=True)
    # Empty count per size
    empty_by_size = {}
    for item in all_inventory:
        if item["FilledWith"] == "Empty":
            empty_by_size[item["BottleSize"]] = empty_by_size.get(item["BottleSize"], 0) + item["Quantity"]
    return render_template("index.html", inventory=inventory, batches=batches,
                           batch_info=batch_info, fermenting=fermenting,
                           empty_capacity=inv.calculate_empty_capacity(),
                           all_bottle_sizes=all_bottle_sizes,
                           empty_by_size=empty_by_size)

if __name__ == "__main__":
    brewfather.update_batches()
    app.run(debug=True, port=8085)