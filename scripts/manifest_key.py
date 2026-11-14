"""Validation and identity derivation for Chrome manifest public keys."""

import base64
import hashlib


_RSA_ENCRYPTION_OID = bytes.fromhex("2a864886f70d010101")


def _read_der(data, offset, expected_tag):
    if offset >= len(data) or data[offset] != expected_tag:
        raise ValueError("Manifest key is not an RSA SubjectPublicKeyInfo DER value")
    offset += 1
    if offset >= len(data):
        raise ValueError("Manifest key has a truncated DER length")
    first_length = data[offset]
    offset += 1
    if first_length < 0x80:
        length = first_length
    else:
        count = first_length & 0x7F
        if count == 0 or count > 4 or offset + count > len(data) or data[offset] == 0:
            raise ValueError("Manifest key has an invalid DER length")
        length = int.from_bytes(data[offset:offset + count], "big")
        if length < 0x80:
            raise ValueError("Manifest key has a noncanonical DER length")
        offset += count
    end = offset + length
    if end > len(data):
        raise ValueError("Manifest key has truncated DER content")
    return data[offset:end], end


def _positive_integer(value):
    if not value or value[0] & 0x80:
        raise ValueError("Manifest RSA key contains an invalid integer")
    if value[0] == 0:
        if len(value) == 1 or not value[1] & 0x80:
            raise ValueError("Manifest RSA key contains a noncanonical integer")
        value = value[1:]
    number = int.from_bytes(value, "big")
    if number <= 0:
        raise ValueError("Manifest RSA key contains a nonpositive integer")
    return number


def decode_manifest_public_key(public_key):
    """Decode and validate a canonical base64 RSA SubjectPublicKeyInfo DER key."""
    if not isinstance(public_key, str) or not public_key:
        raise ValueError("Manifest public key must be a nonempty base64 RSA public key")
    try:
        decoded = base64.b64decode(public_key, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Manifest public key must be standard base64") from exc
    if base64.b64encode(decoded).decode("ascii") != public_key:
        raise ValueError("Manifest public key must use canonical base64 encoding")

    outer, end = _read_der(decoded, 0, 0x30)
    if end != len(decoded):
        raise ValueError("Manifest key has trailing bytes after its DER value")
    algorithm, offset = _read_der(outer, 0, 0x30)
    bit_string, offset = _read_der(outer, offset, 0x03)
    if offset != len(outer) or not bit_string or bit_string[0] != 0:
        raise ValueError("Manifest key has an invalid SubjectPublicKeyInfo bit string")

    oid, algorithm_offset = _read_der(algorithm, 0, 0x06)
    null_parameters, algorithm_offset = _read_der(algorithm, algorithm_offset, 0x05)
    if (oid != _RSA_ENCRYPTION_OID or null_parameters or algorithm_offset != len(algorithm)):
        raise ValueError("Manifest public key must use RSA SubjectPublicKeyInfo DER encoding")

    rsa_key, rsa_end = _read_der(bit_string[1:], 0, 0x30)
    if rsa_end != len(bit_string) - 1:
        raise ValueError("Manifest RSA key has trailing bytes")
    modulus_der, rsa_offset = _read_der(rsa_key, 0, 0x02)
    exponent_der, rsa_offset = _read_der(rsa_key, rsa_offset, 0x02)
    if rsa_offset != len(rsa_key):
        raise ValueError("Manifest RSA key must contain exactly a modulus and exponent")
    modulus = _positive_integer(modulus_der)
    exponent = _positive_integer(exponent_der)
    if modulus.bit_length() < 512 or modulus % 2 == 0 or exponent < 3 or exponent % 2 == 0:
        raise ValueError("Manifest RSA key has invalid public parameters")
    return decoded


def chrome_extension_id(public_key):
    """Return Chrome's stable ID for the manifest's base64-encoded public key."""
    decoded = decode_manifest_public_key(public_key)
    digest = hashlib.sha256(decoded).digest()[:16]
    return "".join(chr(ord("a") + nibble) for byte in digest for nibble in (byte >> 4, byte & 15))
