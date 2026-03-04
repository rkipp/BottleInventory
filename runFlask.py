from flask import Flask, render_template, request, redirect, url_for
from invManagement import Inventory
import brewfather

app = Flask(__name__)
inv = Inventory()


# ----------------------------------------------------------------------
# Edit page — bulk inventory management
# ----------------------------------------------------------------------

@app.route("/edit", methods=["GET", "POST"])
def edit_inventory():
    """Display and handle the bulk inventory edit table.

    POST: Receives parallel lists of BottleSize / Quantity / FilledWith
    and replaces the entire inventory in one operation.
    """
    inv = Inventory()

    if request.method == "POST":
        sizes      = request.form.getlist("BottleSize")
        quantities = request.form.getlist("Quantity")
        filleds    = request.form.getlist("FilledWith")

        new_data = [
            {"BottleSize": size, "Quantity": qty, "FilledWith": filled or "Empty"}
            for size, qty, filled in zip(sizes, quantities, filleds)
        ]
        inv.replace_inventory(new_data)
        return redirect(url_for("edit_inventory"))

    batches = brewfather.get_batches()["name"].to_list()
    return render_template("edit.html", inventory=inv.get_inventory(), batches=batches)


# ----------------------------------------------------------------------
# Home page — inventory overview and quick actions
# ----------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    """Home page showing grouped inventory, fermenter status, and bottling helper.

    POST actions:
        update — sync Brewfather batches and auto-empty archived bottles.
        add    — add new bottles (empty or filled).
        fill   — mark empty bottles as filled with a specific beer.
        empty  — mark filled bottles as empty.
        remove — remove bottles from inventory entirely.
    """
    if request.method == "POST":
        action = request.form["action"]

        if action == "update":
            # Read active names before updating so we have the pre-update state
            active_names = (
                brewfather.get_batches()["name"].to_list()
                + brewfather.get_whats_fermenting()["name"].to_list()
            )
            brewfather.update_batches()
            if active_names:
                inv.auto_empty_archived(active_names)
            return redirect(url_for("index"))

        size        = int(request.form["bottle_size"])
        quantity    = int(request.form["quantity"])
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

    # --- Build template context ---

    inventory   = inv.group_inventory()
    batches_df  = brewfather.get_batches()
    batches     = batches_df["name"].to_list()

    # Per-beer display info (ABV, style, SRM colour)
    batch_info = {
        row["name"]: {
            "abv":   row["measuredAbv"],
            "style": row["style"],
            "color": brewfather.srm_to_hex(row.get("estimatedColor")),
        }
        for row in batches_df.to_dicts()
    }

    # Fermenting vessels for the right-column display
    fermenting_df   = brewfather.get_whats_fermenting()
    fermenting_list = [
        {"name": row["name"], "color": brewfather.srm_to_hex(row.get("estimatedColor"))}
        for row in fermenting_df.to_dicts()
    ]
    fermenting = fermenting_list if fermenting_list else False

    # Bottling helper data: all owned sizes (excl. kegs) and empty counts per size
    all_inventory    = inv.get_inventory()
    all_bottle_sizes = sorted(
        {item["BottleSize"] for item in all_inventory if item["BottleSize"] != 320},
        reverse=True
    )
    empty_by_size = {}
    for item in all_inventory:
        if item["FilledWith"] == "Empty":
            empty_by_size[item["BottleSize"]] = (
                empty_by_size.get(item["BottleSize"], 0) + item["Quantity"]
            )

    return render_template(
        "index.html",
        inventory=inventory,
        batches=batches,
        batch_info=batch_info,
        fermenting=fermenting,
        empty_capacity=inv.calculate_empty_capacity(),
        all_bottle_sizes=all_bottle_sizes,
        empty_by_size=empty_by_size,
    )


if __name__ == "__main__":
    brewfather.update_batches()
    app.run(debug=True, port=8085)