&#x20;🔐 FaceVault — Secure File Encryption \& Face Recognition



FaceVault is a Python-based desktop application designed to protect files using password-based encryption and face recognition authentication. It provides a graphical interface for account management, user authentication, and secure file encryption and decryption.



The project combines biometric authentication, password security, and cryptographic file protection in one application.



&#x20;✨ Features



👤 1. User Registration \& Account Management

\- Create user accounts with login credentials.

\- Store account information in a local SQLite database.

\- Manage account-related vault records.

\- Delete user accounts and their associated database records.



🧑 2. Face Recognition Authentication

\- Capture facial data using a webcam.

\- Detect and recognize faces using OpenCV.

\- Generate numerical face embeddings for facial matching.

\- Compare captured facial data with registered face data.

\- Use password login as a fallback when face authentication is unsuccessful or unavailable.



🔑 3. Password-Based Authentication

\- Authenticate users using their account credentials.

\- Store passwords as salted hashes using `hashlib.scrypt`.

\- Provide an alternative login method if face authentication cannot be completed.



🔒 4. File Encryption

\- Encrypt files using password-derived cryptographic keys.

\- Use Fernet authenticated encryption to protect file contents.

\- Generate a random salt for each encrypted file.

\- Save encrypted files with the `.vault` extension.

\- Support different file types by encrypting their raw bytes.

\- Add a file-format header to identify FaceVault-encrypted files.



🔓 5. File Decryption

\- Decrypt protected files using the correct password.

\- Verify encrypted data integrity during decryption.

\- Display an error if the password is incorrect or the encrypted file is damaged.

\- Restore the decrypted file in the same directory as the encrypted file.

\- Avoid overwriting an existing restored file.



🗑️ 6. Original File \& Encrypted File Management



\*\*After encryption\*\*

\- The encrypted copy is saved with the `.vault` extension.

\- The original file remains in its original location.

\- The original file is not automatically deleted by the encryption function.



\*\*After decryption\*\*

\- The decrypted file is restored alongside the encrypted file.

\- The encrypted `.vault` file remains in place.

\- The encrypted file is not automatically deleted by the decryption function.



\*\*Important:\*\* Users should verify that the encrypted or restored file works correctly before deleting any other copy. Deleting a file normally does not guarantee that its data has been securely erased from storage.



🗄️ 7. Database Management

\- Use SQLite for local account and vault-record storage.

\- Organize user information and file-related records.

\- Support deletion of account records from the database.



\*\*Note:\*\* Deleting an account removes associated database records, but does not automatically erase encrypted files stored on disk.



🖥️ 8. Desktop Graphical User Interface

\- Built using Python Tkinter.

\- Provides a graphical interface for authentication and file operations.

\- Displays error messages and feedback for important actions.

\- Makes encryption and decryption accessible without requiring command-line interaction.



🛠️ Technologies Used



\- \*\*Python\*\* — Core application logic

\- \*\*Tkinter\*\* — Desktop graphical user interface

\- \*\*OpenCV\*\* — Face detection and recognition

\- \*\*NumPy\*\* — Numerical operations and face-embedding data

\- \*\*SQLite\*\* — Local database management

\- \*\*Cryptography (Fernet)\*\* — Authenticated file encryption and decryption

\- \*\*hashlib.scrypt\*\* — Password hashing and cryptographic key derivation



&#x20;📂 Project Structure



```text

FaceVault/

├── src/

│   ├── gui.py

│   ├── database.py

│   ├── face\_engine.py

│   └── crypto\_engine.py

├── models/

├── tests/

├── data/

├── .gitignore

├── requirements.txt

└── README.md

```



The `data/` directory may contain local database files. Personal databases and sensitive data should not be uploaded to a public repository.



&#x20;🚀 Getting Started



\#Prerequisites



\- Python 3.x

\- A webcam for face registration and authentication

\- Required Python packages

\- Required face-recognition model files



\# Installation



\*\*1. Download the project\*\*



Download the repository or clone it using Git if Git is installed.



\*\*2. Install dependencies\*\*



Open a terminal in the project directory and run:



```bash

pip install -r requirements.txt

```



\*\*3. Set up the face-recognition models\*\*



Ensure the required model files are available in the expected `models/` directory.



\*\*4. Run the application\*\*



```bash

python src/gui.py

```



🔐 Security Considerations



\- Passwords are stored as salted scrypt hashes rather than plain-text passwords.

\- File encryption uses Fernet authenticated encryption.

\- Encryption keys are derived from the supplied password and a randomly generated salt.

\- Face embeddings are biometric data and should be treated as sensitive information.

\- Strong, unique passwords are recommended.

\- Decryption requires the correct password.

\- Keep encrypted files and passwords protected.

\- Do not upload personal databases, biometric data, private documents, passwords, or sensitive test files to a public repository.

\- Deleting the original file is not automatic, and ordinary file deletion is not a guarantee of secure data erasure.



🎯 Project Objective



The objective of FaceVault is to combine face recognition, password-based authentication, and cryptographic file protection in a desktop application. It aims to provide a simple way to authenticate users and protect sensitive files while keeping file encryption and decryption easy to use.



🔮 Future Improvements



Possible future enhancements include:



\- A dedicated vault dashboard for managing encrypted files.

\- Optional confirmation before deleting original files.

\- Improved account recovery and credential management.

\- Better handling of large files during encryption and decryption.

\- Secure deletion options and clearer file-management controls.

\- Additional automated tests for authentication and cryptographic operations.



&#x20;👨‍💻 Author



Vinit Kumar



📜 License



No license has been specified yet. Add an appropriate open-source license before allowing others to reuse, modify, or redistribute this project.

