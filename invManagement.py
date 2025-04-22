import csv
import warnings

class Inventory:
    def __init__(self, filename="./Data/bottle_inventory.csv"):
        self.filename = filename
        self.inventory = self.load_inventory()

    def load_inventory(self):
        """Loads inventory from CSV into a list of dictionaries."""
        try:
            with open(self.filename, mode='r') as file:
                reader = csv.DictReader(file)
                return [
                    {'BottleSize': int(row['BottleSize']),
                     'Quantity': int(row['Quantity']),
                     'FilledWith': row['FilledWith'] if row['FilledWith'] != 'None' else None}
                    for row in reader
                ]
        except FileNotFoundError:
            return []  # Return empty inventory if file doesn't exist

    def group_inventory(self):
        """Groups the inventory by filled content."""
        try:
            with open(self.filename, mode='r') as file:
                reader = csv.DictReader(file)
                grouped_inventory = {}
                for row in reader:
                    filled_with = row['FilledWith'] if row['FilledWith'] != 'None' else None
                    if filled_with not in grouped_inventory:
                        grouped_inventory[filled_with] = []
                    grouped_inventory[filled_with].append((row['Quantity'], row['BottleSize']+'oz'))
                return grouped_inventory
        except FileNotFoundError:
            return {}

    def save_inventory(self):
        """Saves the inventory list to a CSV file."""
        with open(self.filename, mode='w', newline='') as file:
            fieldnames = ['BottleSize', 'Quantity', 'FilledWith']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.inventory)

    def add_bottles(self, bottle_size, quantity, filled_with='Empty'):
        """Adds new bottles or updates existing ones."""
        for item in self.inventory:
            if item['BottleSize'] == bottle_size and item['FilledWith'] == filled_with:
                item['Quantity'] += quantity
                break
        else:
            self.inventory.append({'BottleSize': bottle_size, 'Quantity': quantity, 'FilledWith': filled_with})
        self.save_inventory()

    def remove_bottles(self, bottle_size, quantity, filled_with='Empty'):
        """Removes bottles if they exist, reducing the quantity."""
        for item in self.inventory:
            if item['BottleSize'] == bottle_size and item['FilledWith'] == filled_with:
                update_quantity = item['Quantity'] - quantity
                if update_quantity < 0:
                    warnings.warn('Emptied too many bottles, confirm inventory')
                item['Quantity'] = max(0, item['Quantity'] - quantity)  # Prevent negative quantities
                if item['Quantity'] == 0:
                    self.inventory.remove(item)
                break
        self.save_inventory()

    def fill_bottles(self, bottle_size, quantity, filled_with='Empty'):
        """Fills bottles if they exist"""
        self.remove_bottles(bottle_size, quantity, filled_with='Empty')
        self.save_inventory()
        self.add_bottles(bottle_size, quantity, filled_with=filled_with)

    def empty_bottles(self, bottle_size, quantity, filled_with='Empty'):
        """Empties bottles if they exist"""
        self.remove_bottles(bottle_size, quantity, filled_with=filled_with)
        self.save_inventory()
        self.add_bottles(bottle_size, quantity, filled_with='Empty')

    def display_inventory(self):
        """Prints the inventory in a readable format."""
        print('='*30)
        for item in self.inventory:

            print(f"Size: {item['BottleSize']}oz | Quantity: {item['Quantity']} | Filled With: {item['FilledWith']}")
        print('='*30)

