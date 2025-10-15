import json
import bcrypt

def encrypt_passwords(source_file, destination_file):
    """
    Loads user data from a JSON file, hashes the passwords using bcrypt,
    and saves the updated data to a new file.
    """
    try:
        with open(source_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{source_file}' was not found.")
        return

    if 'users' not in data:
        print("Error: The JSON file does not contain a 'users' key.")
        return

    print(f"Loaded {len(data['users'])} users from {source_file}.")

    # Iterate through each user and hash their password
    for user in data['users']:
        if 'password' in user:
            plaintext_password = user['password'].encode('utf-8')

            # Generate a salt and hash the password
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(plaintext_password, salt)

            # Replace the plaintext password with the hashed one (as a string)
            user['password'] = hashed_password.decode('utf-8')

    # Save the updated data to the new file
    with open(destination_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Successfully encrypted passwords and saved the data to '{destination_file}'.")


if __name__ == "__main__":
    # The name of the JSON file you provided me earlier
    source_json_file = "knowledge_base_two.json"
    # The name of the new file that will contain the encrypted data
    encrypted_json_file = "knowledge_base_encrypted.json"

    encrypt_passwords(source_json_file, encrypted_json_file)

    