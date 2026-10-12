from getpass import getpass
import httpx

BASE_URL = "http://127.0.0.1:8011"

# In session cookie authentication, httpx.Client acts like a web browser:
# When the server returns 'Set-Cookie: session_id=...', httpx stores it automatically
# inside client.cookies. Every future request automatically carries the cookie!
# NOTICE: We DO NOT manually set any Authorization headers here!
client = httpx.Client(base_url=BASE_URL)
CURRENT_USER_EMAIL = None
CURRENT_USER_ROLE = None


def register():
    print("\n===== [SESSION COOKIE] REGISTER =====")
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
        response = client.post("/session-user/register", json=user_payload)
        if response.status_code == 201:
            data = response.json()
            print(f"\nRegistration successful! Created {data['email']} with role: {data['role']}")
        else:
            print(f"\nRegistration failed (HTTP {response.status_code}): {response.text}")
    except httpx.ConnectError:
        print("\nCould not connect to server. Ensure FastAPI is running on port 8011.")


def login():
    global CURRENT_USER_EMAIL, CURRENT_USER_ROLE
    print("\n===== [SESSION COOKIE] LOGIN =====")
    email = input("Email: ").strip()
    password = getpass("Password: ").strip()

    try:
        response = client.post(
            "/session-user/login",
            data={"username": email, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            CURRENT_USER_EMAIL = data["email"]
            CURRENT_USER_ROLE = data["role"]

            print("\nLogin successful!")
            print(f"Logged in as: {CURRENT_USER_EMAIL} (Role: {CURRENT_USER_ROLE})")
            print(f"Session cookies received from server: {dict(client.cookies)}")
            print("Notice: No token string was returned or manually copied!")
        else:
            print(f"\nLogin failed (HTTP {response.status_code}): {response.text}")

    except httpx.ConnectError:
        print("\nCould not connect to server. Ensure FastAPI is running on port 8011.")


def logout():
    global CURRENT_USER_EMAIL, CURRENT_USER_ROLE
    try:
        response = client.post("/session-user/logout")
        print(f"\nLogout response: {response.text}")
        CURRENT_USER_EMAIL = None
        CURRENT_USER_ROLE = None
        print(f"Cookies after logout: {dict(client.cookies)}")
    except httpx.ConnectError:
        print("\nCould not connect to server.")


def view_my_profile():
    print("\nAttempting GET /session-user/me (Cookie automatically sent) ...")
    response = client.get("/session-user/me")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")


def test_student_grades():
    print("\nAttempting GET /session-user/student/grades (Student Only) ...")
    response = client.get("/session-user/student/grades")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")


def test_teacher_portal():
    print("\nAttempting GET /session-user/teacher/portal (Teacher Only) ...")
    response = client.get("/session-user/teacher/portal")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")


def menu():
    while True:
        status_line = (
            f"Logged in as: {CURRENT_USER_EMAIL} [{CURRENT_USER_ROLE}]"
            if CURRENT_USER_EMAIL else "Not logged in"
        )
        print("\n" + "=" * 50)
        print("   SESSION COOKIE PORTAL - AUTH & AUTHZ DEMO")
        print(f"   Status: {status_line}")
        print("=" * 50)
        print("1. Register (Student or Teacher)")
        print("2. Log in (Sets session_id cookie)")
        print("3. View My Profile (/session-user/me)")
        print("4. [STUDENT ONLY] View Grades (/session-user/student/grades)")
        print("5. [TEACHER ONLY] Teacher Portal (/session-user/teacher/portal)")
        print("6. Log out (Destroys session on server & deletes cookie)")
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
