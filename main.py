
from getpass import getpass
from pathlib import Path

from database import (
    initialize_database,
    register_user,
    login_user,
    save_vault_file,
    get_user_files,
)
from crypto_engine import encrypt_file, decrypt_file


def vault_menu(user):
    while True:
        print(f"\n===== FACEVAULT: {user['username']} =====")
        print("1. Encrypt a file")
        print("2. Decrypt a file")
        print("3. My encrypted files")
        print("4. Log out")

        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                file_path = input("Enter file path: ").strip().strip('"')
                password = getpass("Create file encryption password: ")

                result = encrypt_file(file_path, password)

                save_vault_file(
                    user["id"],
                    Path(file_path).name,
                    result,
                )

                print(f"File encrypted successfully: {result}")
                print("File record saved to your account.")

            elif choice == "2":
                file_path = input("Enter .vault file path: ").strip().strip('"')
                password = getpass("Enter file decryption password: ")

                result = decrypt_file(file_path, password)
                print(f"File restored successfully: {result}")

            elif choice == "3":
                files = get_user_files(user["id"])

                if not files:
                    print("You have no registered encrypted files yet.")
                else:
                    print("\n--- Your Encrypted Files ---")

                    for file in files:
                        print(f"ID: {file['id']}")
                        print(f"Original name: {file['original_name']}")
                        print(f"Encrypted path: {file['encrypted_path']}")
                        print(f"Added: {file['created_at']}")
                        print("-" * 30)

            elif choice == "4":
                print("Logged out successfully.")
                break

            else:
                print("Invalid choice. Enter 1, 2, 3, or 4.")

        except (ValueError, OSError) as error:
            print(f"Operation failed: {error}")


def main():
    initialize_database()

    while True:
        print("\n========== FACEVAULT ==========")
        print("1. Register")
        print("2. Log in")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            username = input("Create username: ").strip()
            password = getpass("Create account password: ")

            success, message = register_user(username, password)
            print(message)

        elif choice == "2":
            username = input("Username: ").strip()
            password = getpass("Account password: ")

            user = login_user(username, password)

            if user:
                print(f"Welcome, {user['username']}!")
                vault_menu(user)
            else:
                print("Invalid username or password.")

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
