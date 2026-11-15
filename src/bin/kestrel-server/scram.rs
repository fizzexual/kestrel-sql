//! SCRAM-SHA-256 (RFC 5802, RFC 7677) for the server side, built by hand on `sha2`.
//! Channel binding is not offered: there is no TLS, so the only mechanism is `SCRAM-SHA-256`.
use sha2::{Digest, Sha256};

pub const ITERATIONS: u32 = 4096;

const ALPHABET: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

pub fn b64_encode(data: &[u8]) -> String {
    let mut out = String::with_capacity(data.len().div_ceil(3) * 4);
    for chunk in data.chunks(3) {
        let n = (u32::from(chunk[0]) << 16)
            | (u32::from(*chunk.get(1).unwrap_or(&0)) << 8)
            | u32::from(*chunk.get(2).unwrap_or(&0));
        out.push(ALPHABET[(n >> 18) as usize & 63] as char);
        out.push(ALPHABET[(n >> 12) as usize & 63] as char);
        out.push(if chunk.len() > 1 {
            ALPHABET[(n >> 6) as usize & 63] as char
        } else {
            '='
        });
        out.push(if chunk.len() > 2 {
            ALPHABET[n as usize & 63] as char
        } else {
            '='
        });
    }
    out
}

/// Strict standard-alphabet decoder: padding required, no whitespace, canonical trailing bits.
pub fn b64_decode(text: &str) -> Option<Vec<u8>> {
    let bytes = text.as_bytes();
    if bytes.len() & 3 != 0 {
        return None;
    }
    let value = |c: u8| ALPHABET.iter().position(|a| *a == c).map(|p| p as u32);
    let mut out = Vec::with_capacity(bytes.len() / 4 * 3);
    for (i, quad) in bytes.chunks(4).enumerate() {
        let last = (i + 1) * 4 == bytes.len();
        let pad = quad.iter().rev().take_while(|c| **c == b'=').count();
        if pad > 2 || (pad > 0 && !last) {
            return None;
        }
        let mut n = 0u32;
        for (j, c) in quad.iter().enumerate() {
            n <<= 6;
            if j < 4 - pad {
                n |= value(*c)?;
            }
        }
        let triple = [(n >> 16) as u8, (n >> 8) as u8, n as u8];
        let keep = 3 - pad;
        // Reject non-zero bits hidden in the padding: one canonical text per byte string.
        if triple[keep..].iter().any(|b| *b != 0) {
            return None;
        }
        out.extend_from_slice(&triple[..keep]);
    }
    Some(out)
}

/// HMAC-SHA-256 with the key schedule computed once, so PBKDF2 does not redo it per round.
struct Hmac {
    inner: Sha256,
    outer: Sha256,
}

impl Hmac {
    fn new(key: &[u8]) -> Self {
        let mut block = [0u8; 64];
        if key.len() > 64 {
            block[..32].copy_from_slice(&Sha256::digest(key));
        } else {
            block[..key.len()].copy_from_slice(key);
        }
        let mut inner = Sha256::new();
        let mut outer = Sha256::new();
        inner.update(block.map(|b| b ^ 0x36));
        outer.update(block.map(|b| b ^ 0x5c));
        Self { inner, outer }
    }
    fn mac(&self, parts: &[&[u8]]) -> [u8; 32] {
        let mut inner = self.inner.clone();
        for part in parts {
            inner.update(part);
        }
        let mut outer = self.outer.clone();
        outer.update(inner.finalize());
        outer.finalize().into()
    }
}

pub fn hmac_sha256(key: &[u8], message: &[u8]) -> [u8; 32] {
    Hmac::new(key).mac(&[message])
}

/// PBKDF2-HMAC-SHA-256 with a 32-byte output (one block), which is all SCRAM's `Hi()` needs.
pub fn pbkdf2_sha256(password: &[u8], salt: &[u8], iterations: u32) -> [u8; 32] {
    let hmac = Hmac::new(password);
    let mut u = hmac.mac(&[salt, &1u32.to_be_bytes()]);
    let mut t = u;
    for _ in 1..iterations {
        u = hmac.mac(&[&u]);
        for (a, b) in t.iter_mut().zip(u) {
            *a ^= b;
        }
    }
    t
}

/// Comparison whose time does not depend on where the inputs first differ.
pub fn ct_eq(a: &[u8], b: &[u8]) -> bool {
    a.len() == b.len() && a.iter().zip(b).fold(0u8, |acc, (x, y)| acc | (x ^ y)) == 0
}

/// What the server keeps instead of the password.
pub struct Verifier {
    salt: Vec<u8>,
    iterations: u32,
    stored_key: [u8; 32],
    server_key: [u8; 32],
}

impl Verifier {
    pub fn derive(password: &[u8], salt: Vec<u8>, iterations: u32) -> Self {
        let salted = pbkdf2_sha256(password, &salt, iterations);
        let client_key = hmac_sha256(&salted, b"Client Key");
        Self {
            salt,
            iterations,
            stored_key: Sha256::digest(client_key).into(),
            server_key: hmac_sha256(&salted, b"Server Key"),
        }
    }
}

impl Verifier {
    /// A verifier for a user name that does not exist. Salt and keys are a keyed function of the
    /// name, so asking twice gives the same salt (like a real user) and no password can ever
    /// match. Cheap to build, so unknown and known users take the same time.
    pub fn mock(secret: &[u8; 32], user: &str) -> Self {
        let part = |label: &str| {
            let mut message = label.as_bytes().to_vec();
            message.push(0);
            message.extend_from_slice(user.as_bytes());
            hmac_sha256(secret, &message)
        };
        Self {
            salt: part("salt")[..16].to_vec(),
            iterations: ITERATIONS,
            stored_key: part("stored"),
            server_key: part("server"),
        }
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum ScramError {
    /// The client message is not valid SCRAM text; the connection is unusable.
    Malformed(&'static str),
    /// Syntactically valid but the proof does not match (wrong password).
    BadProof,
}

pub struct Server<'a> {
    verifier: &'a Verifier,
    gs2_header: &'static str,
    client_first_bare: String,
    server_first: String,
    nonce: String,
}

fn attribute(part: Option<&str>, name: char) -> Result<&str, ScramError> {
    let part = part.ok_or(ScramError::Malformed("missing attribute"))?;
    let mut chars = part.chars();
    if chars.next() == Some(name) && chars.next() == Some('=') {
        Ok(&part[2..])
    } else {
        Err(ScramError::Malformed("unexpected attribute"))
    }
}

impl<'a> Server<'a> {
    /// `client_first` is the SASLInitialResponse payload; `server_nonce` is fresh randomness
    /// (printable, no comma).
    pub fn start(
        verifier: &'a Verifier,
        client_first: &str,
        server_nonce: &str,
    ) -> Result<Self, ScramError> {
        let (gs2_header, bare) = if let Some(rest) = client_first.strip_prefix("n,,") {
            ("n,,", rest)
        } else if let Some(rest) = client_first.strip_prefix("y,,") {
            ("y,,", rest)
        } else if client_first.starts_with("p=") {
            return Err(ScramError::Malformed("channel binding is not offered"));
        } else {
            return Err(ScramError::Malformed("unsupported gs2 header"));
        };
        let mut parts = bare.split(',');
        attribute(parts.next(), 'n')?; // user name: the startup packet's user is authoritative
        let client_nonce = attribute(parts.next(), 'r')?;
        if client_nonce.is_empty()
            || client_nonce.len() > 256
            || !client_nonce.bytes().all(|c| (0x21..=0x7e).contains(&c))
        {
            return Err(ScramError::Malformed("invalid client nonce"));
        }
        let nonce = format!("{client_nonce}{server_nonce}");
        let server_first = format!(
            "r={nonce},s={},i={}",
            b64_encode(&verifier.salt),
            verifier.iterations
        );
        Ok(Self {
            verifier,
            gs2_header,
            client_first_bare: bare.to_string(),
            server_first,
            nonce,
        })
    }

    pub fn server_first(&self) -> &str {
        &self.server_first
    }

    /// Verifies the client proof and returns the `server-final-message` (`v=...`).
    pub fn finish(self, client_final: &str) -> Result<String, ScramError> {
        let cut = client_final
            .rfind(",p=")
            .ok_or(ScramError::Malformed("missing proof"))?;
        let without_proof = &client_final[..cut];
        let mut parts = without_proof.split(',');
        if attribute(parts.next(), 'c')? != b64_encode(self.gs2_header.as_bytes()) {
            return Err(ScramError::Malformed("channel binding data mismatch"));
        }
        if attribute(parts.next(), 'r')? != self.nonce {
            return Err(ScramError::Malformed("nonce mismatch"));
        }
        let proof = b64_decode(&client_final[cut + 3..])
            .filter(|p| p.len() == 32)
            .ok_or(ScramError::Malformed("invalid proof encoding"))?;
        let auth_message = format!(
            "{},{},{}",
            self.client_first_bare, self.server_first, without_proof
        );
        let signature = hmac_sha256(&self.verifier.stored_key, auth_message.as_bytes());
        let client_key: Vec<u8> = proof.iter().zip(signature).map(|(p, s)| p ^ s).collect();
        if !ct_eq(&Sha256::digest(&client_key), &self.verifier.stored_key) {
            return Err(ScramError::BadProof);
        }
        let server_signature = hmac_sha256(&self.verifier.server_key, auth_message.as_bytes());
        Ok(format!("v={}", b64_encode(&server_signature)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn hex(bytes: &[u8]) -> String {
        bytes.iter().map(|b| format!("{b:02x}")).collect()
    }

    #[test]
    fn base64_round_trips_and_rejects_noncanonical_text() {
        for (raw, text) in [
            (&b""[..], ""),
            (b"f", "Zg=="),
            (b"fo", "Zm8="),
            (b"foo", "Zm9v"),
            (b"foob", "Zm9vYg=="),
            (b"fooba", "Zm9vYmE="),
            (b"foobar", "Zm9vYmFy"),
        ] {
            assert_eq!(b64_encode(raw), text);
            assert_eq!(b64_decode(text).as_deref(), Some(raw));
        }
        for bad in [
            "Zg", "Zg=", "Zh==", "Zm9=v", "Zm9v====", "Z m9v", "Zm8*", "=Zm9",
        ] {
            assert!(b64_decode(bad).is_none(), "{bad}");
        }
    }

    #[test]
    fn hmac_and_pbkdf2_match_published_vectors() {
        // RFC 4231 test case 2.
        assert_eq!(
            hex(&hmac_sha256(b"Jefe", b"what do ya want for nothing?")),
            "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        );
        // RFC 4231 test case 6: a key longer than the block size is hashed first.
        assert_eq!(
            hex(&hmac_sha256(
                &[0xaa; 131],
                b"Test Using Larger Than Block-Size Key - Hash Key First"
            )),
            "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54"
        );
        // PBKDF2-HMAC-SHA256 vectors widely published for "password"/"salt".
        assert_eq!(
            hex(&pbkdf2_sha256(b"password", b"salt", 1)),
            "120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b"
        );
        assert_eq!(
            hex(&pbkdf2_sha256(b"password", b"salt", 4096)),
            "c5e478d59288c841aa530db6845c4c8d962893a001ce4e11a4963873aa98134a"
        );
    }

    // RFC 7677 section 3: user "user", password "pencil".
    const CLIENT_FIRST: &str = "n,,n=user,r=rOprNGfwEbeRWgbNEkqO";
    const SERVER_NONCE: &str = "%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0";
    const SERVER_FIRST: &str =
        "r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,s=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096";
    const CLIENT_FINAL: &str = "c=biws,r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,p=dHzbZapWIk4jUhN+Ute9ytag9zjfMHgsqmmiz7AndVQ=";
    const SERVER_FINAL: &str = "v=6rriTRBi23WpRR/wtup+mMhUZUn/dB5nLTJRsjl95G4=";

    fn rfc_verifier() -> Verifier {
        Verifier::derive(
            b"pencil",
            b64_decode("W22ZaJ0SNY7soEsUEjb6gQ==").unwrap(),
            ITERATIONS,
        )
    }

    #[test]
    fn rfc7677_vector_is_reproduced_exactly() {
        let verifier = rfc_verifier();
        let server = Server::start(&verifier, CLIENT_FIRST, SERVER_NONCE).unwrap();
        assert_eq!(server.server_first(), SERVER_FIRST);
        assert_eq!(server.finish(CLIENT_FINAL).unwrap(), SERVER_FINAL);
    }

    #[test]
    fn tampered_exchanges_are_refused() {
        let verifier = rfc_verifier();
        let start = || Server::start(&verifier, CLIENT_FIRST, SERVER_NONCE).unwrap();
        // Flip one bit of the proof.
        let bad_proof = CLIENT_FINAL.replace("dHzbZapW", "dHzbZapX");
        assert_eq!(start().finish(&bad_proof), Err(ScramError::BadProof));
        // A different password derives a different verifier.
        let other = Verifier::derive(b"Pencil", verifier.salt.clone(), ITERATIONS);
        let server = Server::start(&other, CLIENT_FIRST, SERVER_NONCE).unwrap();
        assert_eq!(server.finish(CLIENT_FINAL), Err(ScramError::BadProof));
        // Wrong nonce, wrong channel-binding data, missing proof, short proof.
        for bad in [
            CLIENT_FINAL.replace("rOprNGfwEbeRWgbNEkqO%", "rOprNGfwEbeRWgbNEkqX%"),
            CLIENT_FINAL.replace("c=biws", "c=eSws"),
            "c=biws,r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0".to_string(),
            CLIENT_FINAL.replace("ndVQ=", "="),
        ] {
            assert!(matches!(
                start().finish(&bad),
                Err(ScramError::Malformed(_))
            ));
        }
        // Channel binding, authzid and garbage in the first message.
        for first in [
            "p=tls-unique,,n=user,r=abc",
            "n,a=someone,n=user,r=abc",
            "n,,r=abc",
            "n,,n=user,r=",
            "",
        ] {
            assert!(
                Server::start(&verifier, first, SERVER_NONCE).is_err(),
                "{first}"
            );
        }
        // "y" (client supports channel binding but thinks the server does not) is allowed.
        let y = Server::start(&verifier, "y,,n=,r=abc", "xyz").unwrap();
        assert!(y.server_first().starts_with("r=abcxyz,s="));
    }
}
