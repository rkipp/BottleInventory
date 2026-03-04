import csv
import warnings


class Inventory:
    """Manages a bottle inventory stored as a CSV file.

    Each row in the CSV represents a group of bottles of the same size
    and fill status, with columns: BottleSize (int oz), Quantity (int),
    FilledWith (str or None).
    """

    def __init__(self, filename="./Data/bottle_inventory.csv"):
        self.filename = filename
        self.inventory = self.load_inventory()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load_inventory(self):
        """Load inventory from CSV into a list of dicts."""
        try:
            with open(self.filename, mode='r') as file:
                reader = csv.DictReader(file)
                return [
                    {
                        'BottleSize': int(row['BottleSize']),
                        'Quantity': int(row['Quantity']),
                        'FilledWith': row['FilledWith'] if row['FilledWith'] != 'None' else None
                    }
                    for row in reader
                ]
        except FileNotFoundError:
            return []

    def save_inventory(self):
        """Persist the current inventory list to CSV."""
        with open(self.filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['BottleSize', 'Quantity', 'FilledWith'])
            writer.writeheader()
            writer.writerows(self.inventory)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_inventory(self):
        """Return the raw inventory as a list of dicts."""
        return self.inventory

    def group_inventory(self):
        """Return filled inventory grouped by beer, sorted by total oz descending.

        Returns a list of dicts:
            [{'name': str, 'bottles': [{'qty': int, 'size': int}], 'total_oz': int}]
        Empty and None entries are excluded.
        """
        try:
            with open(self.filename, mode='r') as file:
                reader = csv.DictReader(file)
                grouped = {}
                for row in reader:
                    if row['FilledWith'] in ['None', 'Empty']:
                        continue
                    name = row['FilledWith']
                    qty = int(row['Quantity'])
                    size = int(row['BottleSize'])
                    if name not in grouped:
                        grouped[name] = {'bottles': [], 'total_oz': 0}
                    grouped[name]['bottles'].append({'qty': qty, 'size': size})
                    grouped[name]['total_oz'] += qty * size

                sorted_items = sorted(grouped.items(), key=lambda x: x[1]['total_oz'], reverse=True)
                return [
                    {'name': name, 'bottles': data['bottles'], 'total_oz': data['total_oz']}
                    for name, data in sorted_items
                ]
        except FileNotFoundError:
            return []

    def calculate_empty_capacity(self):
        """Return total empty bottle capacity in gallons (rounded to 2dp)."""
        total_oz = sum(
            item['BottleSize'] * item['Quantity']
            for item in self.inventory
            if item['FilledWith'] == 'Empty'
        )
        return round(total_oz / 128, 2)

    def display_inventory(self):
        """Print inventory to stdout in a readable format."""
        print('=' * 30)
        for item in self.inventory:
            print(f"Size: {item['BottleSize']}oz | Quantity: {item['Quantity']} | Filled With: {item['FilledWith']}")
        print('=' * 30)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add_bottles(self, bottle_size, quantity, filled_with='Empty'):
        """Add bottles. If a matching row exists, increment its quantity."""
        for item in self.inventory:
            if item['BottleSize'] == bottle_size and item['FilledWith'] == filled_with:
                item['Quantity'] += quantity
                break
        else:
            self.inventory.append({'BottleSize': bottle_size, 'Quantity': quantity, 'FilledWith': filled_with})
        self.save_inventory()

    def remove_bottles(self, bottle_size, quantity, filled_with='Empty'):
        """Remove bottles by decrementing quantity. Warns if over-removing.

        Quantity will never go below 0. Row is deleted when quantity reaches 0.
        """
        for item in self.inventory:
            if item['BottleSize'] == bottle_size and item['FilledWith'] == filled_with:
                if item['Quantity'] - quantity < 0:
                    warnings.warn('Removing more bottles than available — confirm inventory.')
                item['Quantity'] = max(0, item['Quantity'] - quantity)
                if item['Quantity'] == 0:
                    self.inventory.remove(item)
                break
        self.save_inventory()

    def fill_bottles(self, bottle_size, quantity, filled_with='Empty'):
        """Mark empty bottles as filled with the given content."""
        self.remove_bottles(bottle_size, quantity, filled_with='Empty')
        self.add_bottles(bottle_size, quantity, filled_with=filled_with)

    def empty_bottles(self, bottle_size, quantity, filled_with='Empty'):
        """Mark filled bottles as empty."""
        self.remove_bottles(bottle_size, quantity, filled_with=filled_with)
        self.add_bottles(bottle_size, quantity, filled_with='Empty')

    def auto_empty_archived(self, active_names):
        """Empty all bottles filled with beers not in active_names.

        Called after syncing with Brewfather to automatically clear out
        bottles belonging to archived/deleted batches.

        Args:
            active_names: list of batch names that are still active.
        """
        active_set = set(active_names)
        to_empty = [
            (item['BottleSize'], item['Quantity'], item['FilledWith'])
            for item in self.inventory
            if item['FilledWith'] not in (active_set | {'Empty', None})
        ]
        for bottle_size, quantity, filled_with in to_empty:
            self.empty_bottles(bottle_size, quantity, filled_with=filled_with)
        return to_empty

    # ------------------------------------------------------------------
    # Bulk / direct edits (used by the Edit page)
    # ------------------------------------------------------------------

    def update_row(self, index, bottle_size=None, quantity=None, filled_with=None):
        """Update a single inventory row by index."""
        if 0 <= index < len(self.inventory):
            if bottle_size is not None:
                self.inventory[index]['BottleSize'] = int(bottle_size)
            if quantity is not None:
                self.inventory[index]['Quantity'] = int(quantity)
            if filled_with is not None:
                self.inventory[index]['FilledWith'] = filled_with if filled_with != 'None' else None
            self.save_inventory()
        else:
            warnings.warn(f"Row {index} does not exist in inventory.")

    def delete_row(self, index):
        """Delete a single inventory row by index."""
        if 0 <= index < len(self.inventory):
            self.inventory.pop(index)
            self.save_inventory()
        else:
            warnings.warn(f"Row {index} does not exist in inventory.")

    def replace_inventory(self, new_inventory):
        """Replace the entire inventory with a new list of dicts.

        Args:
            new_inventory: list of dicts with keys BottleSize, Quantity, FilledWith.
        """
        self.inventory = [
            {
                'BottleSize': int(item['BottleSize']),
                'Quantity': int(item['Quantity']),
                'FilledWith': item['FilledWith'] if item['FilledWith'] != 'None' else None
            }
            for item in new_inventory
        ]
        self.save_inventory()