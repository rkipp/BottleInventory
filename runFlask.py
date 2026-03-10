import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
from invManagement import Inventory
import brewfather

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

# Password is set via environment variable ADMIN_PASSWORD
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")


# ----------------------------------------------------------------------
# Auth helpers
# ----------------------------------------------------------------------

def login_required(f):
    """Decorator that redirects to login if the user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    """Simple single-password login page."""
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        error = "Incorrect password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ----------------------------------------------------------------------
# Edit page — bulk inventory management (protected)
# ----------------------------------------------------------------------

@app.route("/edit", methods=["GET", "POST"])
@login_required
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

    known = (
        brewfather.get_batches()["name"].to_list()
        + brewfather.get_whats_fermenting()["name"].to_list()
    )
    known_set = set(known)
    # Also preserve any manually entered names already in the inventory
    custom_fills = sorted({
        item["FilledWith"] for item in inv.get_inventory()
        if item["FilledWith"] and item["FilledWith"] not in ("Empty", None) and item["FilledWith"] not in known_set
    })
    all_fills = known + custom_fills
    return render_template("edit.html", inventory=inv.get_inventory(), batches=all_fills)


# ----------------------------------------------------------------------
# Home page — inventory overview and quick actions
# ----------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    """Home page showing grouped inventory, fermenter status, and bottling helper.

    GET:  Public — anyone can view.
    POST: Protected — requires login. Actions: update, add, fill, empty, remove.
    """
    inv = Inventory()

    if request.method == "POST":
        if not session.get("logged_in"):
            return redirect(url_for("login", next=url_for("index")))

        action = request.form["action"]

        if action == "update":
            brewfather.update_batches()
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

    batch_info = {
        row["name"]: {
            "abv":   row["measuredAbv"],
            "style": row["style"],
            "color": brewfather.srm_to_hex(row.get("estimatedColor")),
        }
        for row in batches_df.to_dicts()
    }

    fermenting_df   = brewfather.get_whats_fermenting()
    fermenting_list = [
        {"name": row["name"], "color": brewfather.srm_to_hex(row.get("estimatedColor"))}
        for row in fermenting_df.to_dicts()
    ]
    fermenting = fermenting_list if fermenting_list else False

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
        logged_in=session.get("logged_in", False),
    )


# ----------------------------------------------------------------------
# BJCP Style Guide
# ----------------------------------------------------------------------

@app.route("/bjcp")
def bjcp():
    """Display the BJCP style guide with search, filtering, and inventory cross-reference."""
    import json
    inv = Inventory()

    with open('./Data/bjcp_styleguide-2021.json') as f:
        styles = json.load(f)['beerjson']['styles']

    categories = sorted(set(s['category'] for s in styles))
    highlight  = request.args.get('style', '')

    inventory_by_style = {}
    for item in inv.group_inventory():
        info = brewfather.get_batches().filter(
            __import__('polars').col('name') == item['name']
        ).to_dicts()
        style = info[0].get('style') if info else None
        if style:
            if style not in inventory_by_style:
                inventory_by_style[style] = []
            total  = sum(b['qty'] for b in item['bottles'])
            is_keg = all(b['size'] == 320 for b in item['bottles'])
            inventory_by_style[style].append({'name': item['name'], 'total': total, 'is_keg': is_keg})

    inventory_styles = set(inventory_by_style.keys())

    return render_template(
        "bjcp.html",
        styles=styles,
        categories=categories,
        inventory_styles=inventory_styles,
        inventory_by_style=inventory_by_style,
        highlight=highlight,
        srm_hex=brewfather.srm_to_hex,
    )


# ----------------------------------------------------------------------
# Off-Flavors Reference
# ----------------------------------------------------------------------

@app.route("/offflavors")
def offflavors():
    """Static off-flavors reference page for use during judging."""
    return render_template("offflavors.html")


if __name__ == "__main__":
    brewfather.update_batches()
    app.run(debug=True, port=8085)