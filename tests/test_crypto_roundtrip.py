from src.infrastructure.crypto_utils import CryptoUtils


def test_encrypt_decrypt_roundtrip():
    password = "correct horse battery staple"
    key, salt = CryptoUtils.derive_key(password)

    plaintext = "this is a test secret"
    ciphertext_b64, nonce_b64 = CryptoUtils.encrypt(plaintext, key)

    assert ciphertext_b64 != plaintext
    recovered = CryptoUtils.decrypt(ciphertext_b64, key, nonce_b64)
    assert recovered == plaintext
