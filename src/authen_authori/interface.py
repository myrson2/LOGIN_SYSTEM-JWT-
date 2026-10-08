from getpass import getpass
from http.cookiejar import request_host

import httpx

from authen_authori.userschema import User


def register():
    print("\n===== REGISTER =====")

    email = input("Email: ")
    password = getpass("Password: ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return

    user = User(
        email=email,
        password=password
    )

    try:
        response = httpx.post(
            "http://127.0.0.1:8011/user/register",
            json=user.model_dump(mode="json")
        )

        if response.status_code == 201:
            print("\nRegistration successful!")
            print(response.json())
        else:
            print(f"\nRegistration failed.")
            print(f"Status code: {response.status_code}")

            try:
                print("Error:", response.json())
            except ValueError:
                print("Error:", response.text)

    except httpx.ConnectError:
        print("\nCould not connect to the server.")
        print("Make sure your FastAPI server is running.")

    except httpx.RequestError as e:
        print(f"\nRequest failed: {e}")


def login():
    print("\n===== LOGIN =====")

    email = input("Email: ")
    password = getpass("Password: ")

    user = User(
        email=email,
        password=password
    )

    print(f"\nLogging in as {user.email}...")

    try:
        response = httpx.post(
            "http://127.0.0.1:8011/user/login",
            data={"username": user.email, "password": user.password}
        )

        if response.status_code == 200:
            print("\nLogin successful!")
            print(response.json())
        else:
            print(f"\nLogin failed.")
            print(f"Status code: {response.status_code}")

            try:
                print("Error:", response.json())
            except ValueError:
                print("Error:", response.text)

    except httpx.ConnectError:
        print("\nCould not connect to the server.")
        print("Make sure your FastAPI server is running.")

    except httpx.RequestError as e:
        print(f"\nRequest failed: {e}")


def menu():
    while True:
        print("\n====================")
        print("       MAIN MENU")
        print("====================")
        print("1. Register")
        print("2. Log in")
        print("3. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            register()

        elif choice == "2":
            login()

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")


def main():
    menu()


if __name__ == "__main__":
    main()
