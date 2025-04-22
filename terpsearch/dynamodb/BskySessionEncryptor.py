import os
from cryptography.fernet import Fernet
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants


class BskySessionEncryptor:
    """
    A utility class to handle encryption and decryption of messages using the Fernet symmetric encryption.

    This class retrieves an encryption key from environment variables and uses it for secure message handling.
    """

    def __init__(self):
        self.cipher = self.__get_fernet_key()

    def __get_fernet_key(self):
        """
        Retrieves the Fernet encryption key from environment variables and initializes the Fernet cipher.

        Returns:
            Fernet: A Fernet cipher object used for encryption/decryption.
            None: If the key is not found or invalid.
        """
        try:
            key = os.getenv(DynamoDbConstants.FERNET_KEY)
            cipher = Fernet(key.encode())
            return cipher
        except AttributeError as e:
            print('Could not find BskySessionEncrytor() key')
            raise

    def encrypt(self, msg):
        """
        Encrypts a plain text message using the initialized Fernet cipher.

        Args:
            msg (str): The plain text message to encrypt.

        Returns:
            str: The encrypted message, base64 encoded.
        """
        return self.cipher.encrypt(msg.encode()).decode()

    def decrypt(self, token):
        """
        Decrypts an encrypted message using the initialized Fernet cipher.

        Args:
            token (str): The encrypted message, base64 encoded.

        Returns:
            str: The original plain text message.
        """
        return self.cipher.decrypt(token.encode()).decode()
