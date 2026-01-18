
# Define a function for addition
def add(num1, num2):
    """
    Returns the sum of two numbers.

    Args:
        num1 (float): The first number.
        num2 (float): The second number.

    Returns:
        float: The sum of num1 and num2.
    """
    return num1 + num2

# Define a function for subtraction
def subtract(num1, num2):
    """
    Returns the difference of two numbers.

    Args:
        num1 (float): The first number.
        num2 (float): The second number.

    Returns:
        float: The difference of num1 and num2.
    """
    return num1 - num2

# Define a function for multiplication
def multiply(num1, num2):
    """
    Returns the product of two numbers.

    Args:
        num1 (float): The first number.
        num2 (float): The second number.

    Returns:
        float: The product of num1 and num2.
    """
    return num1 * num2

# Define a function for division
def divide(num1, num2):
    """
    Returns the quotient of two numbers.

    Args:
        num1 (float): The dividend.
        num2 (float): The divisor.

    Returns:
        float: The quotient of num1 and num2.

    Raises:
        ZeroDivisionError: If num2 is zero.
    """
    if num2 == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return num1 / num2

# Main function to handle user input
def main():
    print("Simple Calculator")
    print("-----------------")

    while True:
        print("1. Addition")
        print("2. Subtraction")
        print("3. Multiplication")
        print("4. Division")
        print("5. Quit")

        choice = input("Choose an operation (1-5): ")

        if choice in ["1", "2", "3", "4"]:
            num1 = float(input("Enter the first number: "))
            num2 = float(input("Enter the second number: "))

            if choice == "1":
                print(f"{num1} + {num2} = {add(num1, num2)}")
            elif choice == "2":
                print(f"{num1} - {num2} = {subtract(num1, num2)}")
            elif choice == "3":
                print(f"{num1} * {num2} = {multiply(num1, num2)}")
            elif choice == "4":
                try:
                    print(f"{num1} / {num2} = {divide(num1, num2)}")
                except ZeroDivisionError as e:
                    print(str(e))
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please choose a valid operation.")

# Run the main function
if __name__ == "__main__":
    main()
