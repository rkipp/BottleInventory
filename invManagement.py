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
                    if row['FilledWith'] in ['None', 'Empty']:
                        continue
                    filled_with = row['FilledWith']
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
        

    def calculate_empty_capacity(self):
        """Calculates the total empty capacity in the inventory."""
        total_capacity = sum(item['BottleSize'] * item['Quantity'] for item in self.inventory if item['FilledWith'] == 'Empty')
        return round(total_capacity/128, 2)# Convert to gallons and round to 2 decimal places

    def get_inventory(self):
        """Returns the current inventory as a list of dictionaries."""
        return self.inventory

    def update_row(self, index, bottle_size=None, quantity=None, filled_with=None):
        """Updates a single row in the inventory by index."""
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
        """Deletes a row from the inventory by index."""
        if 0 <= index < len(self.inventory):
            self.inventory.pop(index)
            self.save_inventory()
        else:
            warnings.warn(f"Row {index} does not exist in inventory.")

    def replace_inventory(self, new_inventory):
        """
        Replaces the entire inventory with a new list of dicts.
        Example new_inventory: 
        [{'BottleSize': 12, 'Quantity': 6, 'FilledWith': 'IPA'}, ...]
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