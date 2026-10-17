import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path

import numpy as np

from database import (
    initialize_database,
    register_user,
    login_user,
    save_vault_file,
    get_user_files,
    save_face_embedding,
    get_users_with_faces,
    get_all_users,
    verify_user_password,
    change_user_password,
    delete_user_account,
    get_face_embedding,
)
from face_engine import capture_face_embedding, compare_face_embeddings
from crypto_engine import encrypt_file, decrypt_file


# ---------------- APPEARANCE ----------------

BG = "#101827"
PANEL = "#1B2638"
ACCENT = "#6C63FF"
TEXT = "#F3F4F6"
MUTED = "#A7B0C0"
SECONDARY = "#334155"
DANGER = "#8B3445"
SUCCESS = "#0F766E"

FACE_MATCH_THRESHOLD = 0.363
FACE_MATCH_MARGIN = 0.03


def main():
    initialize_database()

    root = tk.Tk()
    root.title("FaceVault")
    root.geometry("780x760")
    root.minsize(650, 600)
    root.configure(bg=BG)

    current_user = {"user": None}

    # ---------------- MAIN LAYOUT ----------------

    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=24, pady=(16, 4))

    tk.Label(
        header,
        text="FACEVAULT",
        font=("Segoe UI", 13, "bold"),
        bg=BG,
        fg=TEXT,
    ).pack(side="left")

    tk.Label(
        header,
        text="LOCAL FILE VAULT",
        font=("Segoe UI", 9),
        bg=BG,
        fg=MUTED,
    ).pack(side="right")

    panel = tk.Frame(root, bg=PANEL, padx=30, pady=25)
    panel.pack(
        fill="both",
        expand=True,
        padx=24,
        pady=(10, 16),
    )

    def clear_panel():
        for widget in panel.winfo_children():
            widget.destroy()

    def button(parent, label, command, color=ACCENT):
        return tk.Button(
            parent,
            text=label,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=30,
            pady=8,
        )

    def heading(title, subtitle=None):
        tk.Label(
            panel,
            text=title,
            font=("Segoe UI", 22, "bold"),
            bg=PANEL,
            fg=TEXT,
        ).pack(pady=(0, 8))

        if subtitle:
            tk.Label(
                panel,
                text=subtitle,
                font=("Segoe UI", 10),
                bg=PANEL,
                fg=MUTED,
                wraplength=590,
                justify="center",
            ).pack(pady=(0, 14))

    def show_error(title, error):
        messagebox.showerror(title, str(error), parent=root)

    # ---------------- FACE CAPTURE ----------------

    def capture_embedding(title):
        """
        Return a validated 128-element face embedding, or None.

        Camera errors and missing faces are reported so the caller
        can offer password verification where appropriate.
        """
        try:
            embedding = capture_face_embedding()

        except Exception as error:
            messagebox.showerror(
                "Camera Not Working",
                "Face capture could not be completed.\n\n"
                "Check that your camera is connected, available, "
                "and permitted to be used by this application.\n\n"
                f"Details: {error}",
                parent=root,
            )
            return None

        if embedding is None:
            messagebox.showwarning(
                title,
                "No face was detected or captured.\n\n"
                "Try again with your face clearly visible.",
                parent=root,
            )
            return None

        try:
            vector = np.asarray(
                embedding, dtype=np.float32
            ).reshape(-1)
        except (TypeError, ValueError) as error:
            show_error("Face Recognition Error", error)
            return None

        if vector.size != 128 or not np.all(np.isfinite(vector)):
            messagebox.showerror(
                "Face Recognition Error",
                "The face engine returned an invalid feature vector.",
                parent=root,
            )
            return None

        return vector

    def face_matches_user(user_id):
        """Capture a face and compare it only to the selected account."""
        stored_bytes = get_face_embedding(user_id)

        if stored_bytes is None:
            messagebox.showinfo(
                "Face Login Unavailable",
                "This account does not have registered face data.",
                parent=root,
            )
            return False

        captured = capture_embedding("Face Verification")
        if captured is None:
            return False

        try:
            stored = np.frombuffer(
                stored_bytes, dtype=np.float32
            )

            if (
                stored.size != captured.size
                or not np.all(np.isfinite(stored))
            ):
                messagebox.showerror(
                    "Face Data Error",
                    "The registered face data is invalid. "
                    "Use password verification instead.",
                    parent=root,
                )
                return False

            score = compare_face_embeddings(captured, stored)

        except Exception as error:
            messagebox.showerror(
                "Face Recognition Error",
                "Face comparison could not be completed.\n\n"
                f"Details: {error}",
                parent=root,
            )
            return False

        if score >= FACE_MATCH_THRESHOLD:
            return True

        messagebox.showwarning(
            "Face Not Recognized",
            "The captured face did not match this account.\n\n"
            "You can continue using password verification.",
            parent=root,
        )
        return False

    # ---------------- HOME ----------------

    def show_home():
        clear_panel()

        heading(
            "Welcome to FaceVault",
            "Secure your files with face recognition and encryption.",
        )

        button(
            panel, "Create Account", show_register
        ).pack(pady=6)

        button(
            panel, "Login", show_account_login
        ).pack(pady=6)
        
        button(
            panel, "Delete Account", show_delete_account, DANGER
        ).pack(pady=6)

        button(
            panel, "Exit", close_application, DANGER
        ).pack(pady=(18, 6))

    # ---------------- REGISTRATION ----------------

    def show_register():
        clear_panel()
        heading("Create Account", "Choose a username and password.")

        tk.Label(
            panel, text="Username", bg=PANEL, fg=TEXT
        ).pack()

        username_entry = tk.Entry(
            panel, font=("Segoe UI", 12), width=30
        )
        username_entry.pack(pady=(4, 12))

        tk.Label(
            panel, text="Password (at least 8 characters)",
            bg=PANEL, fg=TEXT,
        ).pack()

        password_entry = tk.Entry(
            panel, font=("Segoe UI", 12), width=30, show="*"
        )
        password_entry.pack(pady=(4, 12))

        tk.Label(
            panel, text="Confirm Password",
            bg=PANEL, fg=TEXT,
        ).pack()

        confirm_entry = tk.Entry(
            panel, font=("Segoe UI", 12), width=30, show="*"
        )
        confirm_entry.pack(pady=(4, 12))

        def submit():
            username = username_entry.get().strip()
            password = password_entry.get()
            confirmation = confirm_entry.get()

            if not username or not password:
                messagebox.showwarning(
                    "Missing Details",
                    "Enter a username and password.",
                    parent=root,
                )
                return

            if password != confirmation:
                messagebox.showerror(
                    "Password Mismatch",
                    "The passwords do not match.",
                    parent=root,
                )
                return

            success, message = register_user(username, password)

            if not success:
                messagebox.showerror(
                    "Registration Failed", message, parent=root
                )
                return

            user = login_user(username, password)

            if not user:
                messagebox.showerror(
                    "Registration Error",
                    "The account was created, but automatic login failed. "
                    "Please log in using your password.",
                    parent=root,
                )
                show_account_login()
                return

            current_user["user"] = user

            messagebox.showinfo(
                "Account Created",
                "Your account has been created successfully.",
                parent=root,
            )

            if messagebox.askyesno(
                "Register Your Face",
                "Would you like to register your face now?",
                parent=root,
            ):
                enroll_face()
            else:
                show_dashboard()

        button(panel, "Create Account", submit).pack(pady=8)
        button(
            panel, "Back", show_home, SECONDARY
        ).pack(pady=4)

        username_entry.focus_set()

    # ---------------- ACCOUNT SELECTION ----------------

    def build_account_list(title, subtitle, on_select):
        """
        Display existing accounts in a selectable list.
        on_select receives the selected account dictionary.
        """
        clear_panel()
        heading(title, subtitle)

        try:
            users = get_all_users()
        except Exception as error:
            show_error("Could Not Load Accounts", error)
            button(
                panel, "Back", show_home, SECONDARY
            ).pack(pady=8)
            return

        if not users:
            tk.Label(
                panel,
                text="No registered accounts were found.",
                bg=PANEL,
                fg=MUTED,
            ).pack(pady=15)

            button(
                panel, "Create Account", show_register
            ).pack(pady=5)

            button(
                panel, "Back", show_home, SECONDARY
            ).pack(pady=5)
            return

        listing = tk.Listbox(
            panel,
            width=48,
            height=min(8, len(users)),
            font=("Segoe UI", 11),
            bg="#0F172A",
            fg=TEXT,
            selectbackground=ACCENT,
            selectforeground="white",
            activestyle="dotbox",
            exportselection=False,
        )
        listing.pack(pady=8)

        for account in users:
            listing.insert(tk.END, account["username"])

        def select_account():
            selected = listing.curselection()

            if not selected:
                messagebox.showwarning(
                    "Select an Account",
                    "Choose an account from the list.",
                    parent=root,
                )
                return

            on_select(users[selected[0]])

        listing.bind("<Double-Button-1>", lambda event: select_account())

        button(
            panel, "Continue", select_account
        ).pack(pady=6)

        button(
            panel, "Back", show_home, SECONDARY
        ).pack(pady=4)

        listing.selection_set(0)
        listing.focus_set()

    # ---------------- LOGIN ----------------

    def show_account_login():
        build_account_list(
            "Select Your Account",
            "Face verification is attempted first. "
            "If it fails, you can use your password.",
            start_face_login,
        )

    def start_face_login(account):
        """
        Attempt face login for the selected account only.
        Password fallback remains available after any failed attempt.
        """
        clear_panel()
        heading(
            "Face Login",
            f"Selected account: {account['username']}",
        )

        tk.Label(
            panel,
            text="Look at the camera when face capture begins.",
            bg=PANEL,
            fg=MUTED,
            wraplength=480,
        ).pack(pady=8)

        def attempt_face():
            # Avoid accidentally using a different account's face.
            try:
                matched = face_matches_user(account["id"])
            except Exception as error:
                show_error("Face Login Error", error)
                matched = False

            if matched:
                current_user["user"] = {
                    "id": account["id"],
                    "username": account["username"],
                }
                messagebox.showinfo(
                    "Login Successful",
                    f"Welcome, {account['username']}!",
                    parent=root,
                )
                show_dashboard()
                return

            
            messagebox.showerror(
                "Face Recognition Failed",
                "No matching face was detected, or face recognition failed.\n\n"
                "Please log in with your password.",
                parent=root,
            )
            show_password_login(account)


        button(
            panel, "Start Face Detection", attempt_face
        ).pack(pady=8)

        button(
            panel, "Use Password Instead",
            lambda: show_password_login(account),
            SECONDARY,
        ).pack(pady=6)

        button(
            panel, "Back to Accounts",
            show_account_login, SECONDARY,
        ).pack(pady=4)

    def show_password_login(account):
        clear_panel()
        heading(
            "Login with Password",
            f"Account: {account['username']}",
        )

        tk.Label(
            panel, text="Password", bg=PANEL, fg=TEXT
        ).pack()

        password_entry = tk.Entry(
            panel, font=("Segoe UI", 12), width=30, show="*"
        )
        password_entry.pack(pady=8)

        def submit():
            password = password_entry.get()

            if not password:
                messagebox.showwarning(
                    "Missing Password",
                    "Enter your password.",
                    parent=root,
                )
                return

            user = login_user(account["username"], password)

            if user is None or user["id"] != account["id"]:
                messagebox.showerror(
                    "Login Failed",
                    "Incorrect password. Please try again.",
                    parent=root,
                )
                password_entry.delete(0, tk.END)
                password_entry.focus_set()
                return

            current_user["user"] = user
            messagebox.showinfo(
                "Login Successful",
                f"Welcome, {user['username']}!",
                parent=root,
            )
            show_dashboard()

        button(panel, "Login", submit).pack(pady=8)

        button(
            panel, "Back to Face Login",
            lambda: start_face_login(account), SECONDARY,
        ).pack(pady=4)

        button(
            panel, "Back to Accounts",
            show_account_login, SECONDARY,
        ).pack(pady=4)

        password_entry.bind("<Return>", lambda event: submit())
        password_entry.focus_set()

    # ---------------- FACE REGISTRATION ----------------

    def enroll_face():
        user = current_user["user"]

        if not user:
            show_account_login()
            return

        if not messagebox.askyesno(
            "Register Face",
            "FaceVault will capture your face to enable face login.\n\n"
            "Make sure your face is clearly visible. Continue?",
            parent=root,
        ):
            show_dashboard()
            return

        embedding = capture_embedding("Register Face")

        if embedding is None:
            if messagebox.askyesno(
                "Try Again?",
                "Face registration did not complete. Try again?",
                parent=root,
            ):
                enroll_face()
            else:
                show_dashboard()
            return

        try:
            success, message = save_face_embedding(
                user["id"], embedding
            )
        except Exception as error:
            show_error("Face Registration Failed", error)
            show_dashboard()
            return

        if success:
            messagebox.showinfo(
                "Face Registered",
                "Your face data was saved for this account.",
                parent=root,
            )
        else:
            messagebox.showerror(
                "Face Registration Failed",
                message,
                parent=root,
            )

        show_dashboard()

    # ---------------- CHANGE PASSWORD ----------------

    def change_password():
        user = current_user["user"]

        if not user:
            show_home()
            return

        clear_panel()
        heading(
            "Change Password",
            "Verify your identity using your registered face "
            "or your current password.",
        )

        def verify_by_face():
            if face_matches_user(user["id"]):
                enter_new_password()
                return

            if messagebox.askyesno(
                "Use Current Password?",
                "Face verification failed or was unavailable.\n\n"
                "Would you like to verify using your current password?",
                parent=root,
            ):
                verify_by_password()

        def verify_by_password():
            password = simpledialog.askstring(
                "Verify Current Password",
                "Enter your current account password:",
                show="*",
                parent=root,
            )

            if password is None:
                return

            try:
                valid = verify_user_password(user["id"], password)
            except Exception as error:
                show_error("Password Verification Failed", error)
                return

            if not valid:
                messagebox.showerror(
                    "Verification Failed",
                    "The current password is incorrect.",
                    parent=root,
                )
                return

            enter_new_password()

        def enter_new_password():
            new_password = simpledialog.askstring(
                "New Password",
                "Enter your new password (at least 8 characters):",
                show="*",
                parent=root,
            )

            if new_password is None:
                return

            confirmation = simpledialog.askstring(
                "Confirm New Password",
                "Enter the new password again:",
                show="*",
                parent=root,
            )

            if confirmation is None:
                return

            if len(new_password) < 8:
                messagebox.showerror(
                    "Invalid Password",
                    "The new password must contain at least 8 characters.",
                    parent=root,
                )
                return

            if new_password != confirmation:
                messagebox.showerror(
                    "Password Mismatch",
                    "The new passwords do not match.",
                    parent=root,
                )
                return

            try:
                success, message = change_user_password(
                    user["id"], new_password
                )
            except Exception as error:
                show_error("Password Change Failed", error)
                return

            if success:
                messagebox.showinfo(
                    "Password Changed", message, parent=root
                )
                show_dashboard()
            else:
                messagebox.showerror(
                    "Password Change Failed",
                    message,
                    parent=root,
                )

        button(
            panel, "Verify with Face", verify_by_face
        ).pack(pady=6)

        button(
            panel, "Verify with Current Password",
            verify_by_password, SECONDARY,
        ).pack(pady=6)

        button(
            panel, "Back to Dashboard",
            show_dashboard, SECONDARY,
        ).pack(pady=6)

    # ---------------- DELETE ACCOUNT ----------------

    def show_delete_account():
        build_account_list(
            "Delete Account",
            "Select the account to delete. You must know its password.",
            confirm_account_deletion,
        )

    def confirm_account_deletion(account):
        password = simpledialog.askstring(
            "Verify Account Password",
            f"Enter the password for '{account['username']}':",
            show="*",
            parent=root,
        )

        if password is None:
            return

        try:
            valid = verify_user_password(account["id"], password)
        except Exception as error:
            show_error("Password Verification Failed", error)
            return

        if not valid:
            messagebox.showerror(
                "Verification Failed",
                "Incorrect password. The account was not deleted.",
                parent=root,
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm Account Deletion",
            f"Are you sure you want to delete '{account['username']}'?\n\n"
            "This removes the account and its database file records.\n"
            "Encrypted files on disk will NOT be deleted.\n\n"
            "This action cannot be undone.",
            icon="warning",
            parent=root,
        )

        if not confirmed:
            return

        try:
            success, message = delete_user_account(account["id"])
        except Exception as error:
            show_error("Account Deletion Failed", error)
            return

        if not success:
            messagebox.showerror(
                "Account Deletion Failed", message, parent=root
            )
            return

        # If the currently logged-in account was deleted, log out.
        logged_in = current_user["user"]
        if logged_in and logged_in["id"] == account["id"]:
            current_user["user"] = None

        messagebox.showinfo(
            "Account Deleted", message, parent=root
        )
        show_account_login()

    # ---------------- ENCRYPT FILE ----------------

    def encrypt_selected_file():
        user = current_user["user"]

        if not user:
            show_home()
            return

        path = filedialog.askopenfilename(
            parent=root,
            title="Select a file to encrypt",
        )

        if not path:
            return

        source_path = Path(path).resolve()

        secret = simpledialog.askstring(
            "Encryption Password",
            "Create a password for this file:",
            show="*",
            parent=root,
        )

        if not secret:
            return

        encrypted_path = None

        try:
            encrypted_path = Path(
                encrypt_file(str(source_path), secret)
            ).resolve()

            if (
                not encrypted_path.is_file()
                or encrypted_path == source_path
                or encrypted_path.stat().st_size == 0
            ):
                raise OSError(
                    "Encrypted file verification failed. "
                    "The original has been kept."
                )

            save_vault_file(
                user["id"],
                source_path.name,
                str(encrypted_path),
            )

        except (ValueError, OSError, sqlite3.Error) as error:
            # Import sqlite3 below is unnecessary for typical file failures,
            # but database errors should not leave a misleading success.
            messagebox.showerror(
                "Encryption Failed",
                str(error),
                parent=root,
            )
            return
        except Exception as error:
            messagebox.showerror(
                "Encryption Failed",
                str(error),
                parent=root,
            )
            return

        delete_original = messagebox.askyesno(
            "Encryption Complete",
            f"Encrypted file created:\n{encrypted_path}\n\n"
            f"Original file:\n{source_path}\n\n"
            "Do you want to delete the original unencrypted file?",
            parent=root,
        )

        if delete_original:
            try:
                if (
                    not encrypted_path.is_file()
                    or encrypted_path.stat().st_size == 0
                ):
                    raise OSError(
                        "The encrypted copy is missing or empty. "
                        "The original file has not been deleted."
                    )

                source_path.unlink()

            except OSError as error:
                messagebox.showerror(
                    "Original Kept",
                    "Encryption was completed, but the original file "
                    f"could not be deleted:\n{error}",
                    parent=root,
                )
                return

            messagebox.showinfo(
                "Success",
                "The original file was deleted from its previous location.\n\n"
                "The encrypted copy remains in FaceVault. "
                "Test decryption to verify recovery.",
                parent=root,
            )
        else:
            messagebox.showinfo(
                "Success",
                "The encrypted copy was saved. "
                "The original file was kept.",
                parent=root,
            )

    # ---------------- DECRYPT FILE ----------------

    def decrypt_selected_file():
        user = current_user["user"]

        if not user:
            show_home()
            return

        try:
            files = get_user_files(user["id"])
        except Exception as error:
            show_error("Could Not Load Files", error)
            return

        if not files:
            messagebox.showinfo(
                "No Files",
                "Your account has no registered encrypted files.",
                parent=root,
            )
            return

        registered_files = [
            (
                str(Path(file["encrypted_path"]).resolve()),
                file["original_name"],
            )
            for file in files
        ]

        selection_window = tk.Toplevel(root)
        selection_window.title("My Encrypted Files")
        selection_window.geometry("720x420")
        selection_window.configure(bg=PANEL)
        selection_window.transient(root)
        selection_window.grab_set()

        tk.Label(
            selection_window,
            text="Select a registered encrypted file",
            font=("Segoe UI", 13, "bold"),
            bg=PANEL,
            fg=TEXT,
        ).pack(pady=12)

        listing = tk.Listbox(
            selection_window,
            width=85,
            height=12,
            font=("Consolas", 9),
            bg="#0F172A",
            fg=TEXT,
            selectbackground=ACCENT,
            exportselection=False,
        )
        listing.pack(fill="both", expand=True, padx=12, pady=8)

        for path, original_name in registered_files:
            listing.insert(tk.END, f"{original_name}  |  {path}")

        def decrypt_choice():
            selected = listing.curselection()

            if not selected:
                messagebox.showwarning(
                    "Select a File",
                    "Please select a file from the list.",
                    parent=selection_window,
                )
                return

            selected_path, _ = registered_files[selected[0]]

            try:
                current_files = get_user_files(user["id"])
                allowed_paths = {
                    str(Path(file["encrypted_path"]).resolve())
                    for file in current_files
                }
            except Exception as error:
                messagebox.showerror(
                    "Access Check Failed",
                    str(error),
                    parent=selection_window,
                )
                return

            if selected_path not in allowed_paths:
                messagebox.showerror(
                    "Access Denied",
                    "This file is not registered to your account.",
                    parent=selection_window,
                )
                return

            if not Path(selected_path).is_file():
                messagebox.showerror(
                    "File Not Found",
                    "The encrypted file does not exist at its saved path.",
                    parent=selection_window,
                )
                return

            secret = simpledialog.askstring(
                "Decryption Password",
                "Enter this file's encryption password:",
                show="*",
                parent=selection_window,
            )

            if not secret:
                return

            try:
                restored_path = decrypt_file(selected_path, secret)

                messagebox.showinfo(
                    "Decryption Complete",
                    f"Restored file created:\n{restored_path}",
                    parent=selection_window,
                )

                selection_window.destroy()

            except (ValueError, OSError) as error:
                messagebox.showerror(
                    "Decryption Failed",
                    str(error),
                    parent=selection_window,
                )

        button(
            selection_window,
            "Decrypt Selected File",
            decrypt_choice,
        ).pack(pady=10)

        button(
            selection_window,
            "Close",
            selection_window.destroy,
            SECONDARY,
        ).pack(pady=(0, 10))

    # ---------------- FILE LIST ----------------

    def show_files():
        user = current_user["user"]

        if not user:
            show_home()
            return

        clear_panel()
        heading("My Encrypted Files")

        try:
            files = get_user_files(user["id"])
        except Exception as error:
            show_error("Could Not Load Files", error)
            show_dashboard()
            return

        listing = tk.Listbox(
            panel,
            width=75,
            height=12,
            font=("Consolas", 9),
            bg="#0F172A",
            fg=TEXT,
            selectbackground=ACCENT,
            exportselection=False,
        )
        listing.pack(fill="both", expand=True, pady=8)

        if not files:
            listing.insert(tk.END, "No registered encrypted files yet.")
        else:
            for file in files:
                listing.insert(
                    tk.END,
                    f"{file['original_name']} | {file['encrypted_path']}",
                )

        button(
            panel, "Back to Dashboard",
            show_dashboard, SECONDARY,
        ).pack(pady=8)

    # ---------------- LOGOUT / EXIT ----------------

    def logout():
        current_user["user"] = None
        show_home()

    def close_application():
        root.destroy()

    # ---------------- DASHBOARD ----------------

    def show_dashboard():
        user = current_user["user"]

        if not user:
            show_home()
            return

        clear_panel()

        heading(
            "Your Dashboard",
            f"Logged in as {user['username']}",
        )

        button(
            panel, "Encrypt a File", encrypt_selected_file
        ).pack(pady=4)

        button(
            panel, "Decrypt a File", decrypt_selected_file
        ).pack(pady=4)

        button(
            panel, "My Encrypted Files",
            show_files, SECONDARY,
        ).pack(pady=4)

        button(
            panel, "Change Password",
            change_password, SECONDARY,
        ).pack(pady=4)

        button(
            panel, "Delete Account",
            show_delete_account, DANGER,
        ).pack(pady=4)

        button(
            panel, "Set Up / Update Face Login",
            enroll_face, SUCCESS,
        ).pack(pady=4)

        button(
            panel, "Log Out", logout, DANGER
        ).pack(pady=(12, 4))

    # ---------------- START ----------------

    root.protocol("WM_DELETE_WINDOW", close_application)
    show_home()
    root.mainloop()


if __name__ == "__main__":
    main()
