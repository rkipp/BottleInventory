import sys
from invManagement import Inventory

def print_menu():
    print("\nInventory Management CLI")
    print("1. View Inventory")
    print("2. Add Bottles")
    print("3. Fill Bottles")
    print("4. Empty Bottles")
    print("5. Exit")

def main():
    inv = Inventory()

    while True:
        print_menu()
        choice = input("Enter choice: ")

        if choice == "1":
            inv.display_inventory()

        elif choice == "2":
            try:
                size = int(input("Enter bottle size (oz): "))
                qty = int(input("Enter quantity to add: "))
                filled_with = input("Enter contents (leave empty for None): ") or None
                inv.add_bottles(size, qty, filled_with)
                print("Bottles added successfully.")
            except ValueError:
                print("Invalid input. Please enter numbers for size and quantity.")

        elif choice == "3":
            try:
                size = int(input("Enter bottle size (oz): "))
                qty = int(input("Enter quantity to fill: "))
                filled_with = input("Enter what you're filling it with: ")
                inv.fill_bottles(size, qty, filled_with)
            except ValueError:
                print("Invalid input. Please enter numbers for size and quantity. Use 'Empty' for empty bottles.")

        elif choice == "4":
            try:
                size = int(input("Enter bottle size (oz): "))
                qty = int(input("Enter quantity to empty: "))
                filled_with = input("Enter what you emptied: ")
                inv.empty_bottles(size, qty, filled_with)
            except ValueError:
                print("Invalid input. Please enter numbers for size and quantity. Use 'Empty' for empty bottles.")
        
        elif choice == "5":
            print("Exiting inventory manager.")
            sys.exit()

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
