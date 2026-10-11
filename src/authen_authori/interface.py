from getpass import getpass
import httpx

from authen_authori.userschema import User

BASE_URL = "http://127.0.0.1:8011"

# Option 3: Persistent HTTP Client
# When login succeeds, we update client.headers with 'Authorization: Bearer <token>'
# From then on, EVERY request automatically includes the token.
client = httpx.Client(base_url=BASE_URL)
CURRENT_USER_EMAIL = None
CURRENT_USER_ROLE = None


def register():
    print("\n===== REGISTER =====")
    email = input("Email (must end with @example.com): ").strip()
    password = getpass("Password (min 8 chars): ").strip()
    confirm_password = getpass("Confirm password: ").strip()

    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    print("\nSelect Role:")
    print("1. student")
    print("2. teacher")
    role_choice = input("Choice (1/2, default 1): ").strip()
    role = "teacher" if role_choice == "2" else "student"

    user_payload = {
        "email": email,
        "password": password,
        "role": role
    }

    try:
        response = client.post("/user/register", json=user_payload)
        if response.status_code == 201:
            data = response.json()
            print(f"\nRegistration successful! Created {data['email']} with role: {data['role']}")
        else:
            print(f"\nRegistration failed (HTTP {response.status_code}): {response.text}")
    except httpx.ConnectError:
        print("\nCould not connect to server. Ensure FastAPI is running on port 8011.")


def login():
    global CURRENT_USER_EMAIL, CURRENT_USER_ROLE
    print("\n===== LOGIN =====")
    email = input("Email: ").strip()
    password = getpass("Password: ").strip()

    try:
        # OAuth2 password flow expects form data: username & password
        response = client.post(
            "/user/login",
            data={"username": email, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]

            # ---> OPTION 3 IN ACTION <---
            # Store the token inside the client's default headers:
            client.headers.update({"Authorization": f"Bearer {token}"})

            # Fetch our user profile to confirm who we are
            me_resp = client.get("/user/me")
            if me_resp.status_code == 200:
                me_data = me_resp.json()
                CURRENT_USER_EMAIL = me_data["email"]
                CURRENT_USER_ROLE = me_data["role"]
                print(f"\nLogin successful!")
                print(f"Logged in as: {CURRENT_USER_EMAIL} (Role: {CURRENT_USER_ROLE})")
                print("Token is now stored in client.headers for all future requests!")
            else:
                print("\nLogged in, but failed to fetch profile.")
        else:
            print(f"\nLogin failed (HTTP {response.status_code}): {response.text}")

    except httpx.ConnectError:
        print("\nCould not connect to server. Ensure FastAPI is running on port 8011.")


def logout():
    global CURRENT_USER_EMAIL, CURRENT_USER_ROLE
    if "Authorization" in client.headers:
        del client.headers["Authorization"]
    CURRENT_USER_EMAIL = None
    CURRENT_USER_ROLE = None
    print("\nLogged out. Token cleared from client.")


def test_student_grades():
    print("\nAttempting to access: GET /user/student/grades ...")
    response = client.get("/user/student/grades")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")


def test_teacher_portal():
    print("\nAttempting to access: GET /user/teacher/portal ...")
    response = client.get("/user/teacher/portal")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")


def view_my_profile():
    print("\nAttempting to access: GET /user/me ...")
    response = client.get("/user/me")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")


def menu():
    while True:
        status_line = (
            f"Logged in as: {CURRENT_USER_EMAIL} [{CURRENT_USER_ROLE}]"
            if CURRENT_USER_EMAIL else "Not logged in"
        )
        print("\n" + "=" * 45)
        print("   SCHOOL PORTAL - AUTH & AUTHZ DEMO")
        print(f"   Status: {status_line}")
        print("=" * 45)
        print("1. Register (Student or Teacher)")
        print("2. Log in")
        print("3. View My Profile (/user/me)")
        print("4. [STUDENT ONLY] View Grades (/user/student/grades)")
        print("5. [TEACHER ONLY] Teacher Portal (/user/teacher/portal)")
        print("6. Log out")
        print("7. Exit")

        choice = input("\nChoose an option (1-7): ").strip()

        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            view_my_profile()
        elif choice == "4":
            test_student_grades()
        elif choice == "5":
            test_teacher_portal()
        elif choice == "6":
            logout()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose between 1 and 7.")


if __name__ == "__main__":
    menu()
