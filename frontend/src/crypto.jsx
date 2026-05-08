export function modPow(base, exp, mod) {
  ;[base, exp, mod] = [BigInt(base), BigInt(exp), BigInt(mod)]
  let result = 1n
  base %= mod
  while (exp > 0n) {
    if (exp & 1n) result = (result * base) % mod
    exp >>= 1n
    base = (base * base) % mod
  }
  return result
}

function gcd(a, b) {
  ;[a, b] = [BigInt(a), BigInt(b)]
  while (b !== 0n) [a, b] = [b, a % b]
  return a < 0n ? -a : a
}

function modInverse(a, m) {
  ;[a, m] = [BigInt(a), BigInt(m)]
  let [oldR, r] = [a, m]
  let [oldS, s] = [1n, 0n]
  while (r !== 0n) {
    const q = oldR / r
    ;[oldR, r] = [r, oldR - q * r]
    ;[oldS, s] = [s, oldS - q * s]
  }
  if (oldR !== 1n) throw new Error('Inverse impossible')
  return ((oldS % m) + m) % m
}

function randomBigIntBelow(maxExclusive) {
  const max = BigInt(maxExclusive)
  if (max <= 2n) return 1n
  const bits = max.toString(2).length
  const bytes = Math.ceil(bits / 8)
  while (true) {
    const arr = new Uint8Array(bytes)
    crypto.getRandomValues(arr)
    let x = 0n
    for (const b of arr) x = (x << 8n) | BigInt(b)
    const extraBits = bytes * 8 - bits
    if (extraBits > 0) x &= (1n << BigInt(bits)) - 1n
    if (x > 1n && x < max) return x
  }
}

function randomCoprime(N) {
  const n = BigInt(N)
  if (n <= 3n) return 2n
  while (true) {
    const k = randomBigIntBelow(n)
    if (k > 1n && gcd(k, n) === 1n) return k
  }
}

export async function prepareBlindSignature(choiceIdx, N2, admin_e, admin_N) {
  const ballotStr = `${choiceIdx}|${N2}`
  const hashBuf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ballotStr))
  let h = 0n
  for (const b of new Uint8Array(hashBuf)) h = (h << 8n) | BigInt(b)
  const m_int = (h % (admin_N - 1n)) + 1n

  const k = randomCoprime(admin_N)
  const k_e = modPow(k, admin_e, admin_N)
  const m_masked = (m_int * k_e) % admin_N

  return { m_int, k, m_masked }
}

export function unblindSignature(s_blind, k, admin_N) {
  const k_inv = modInverse(k, admin_N)
  return (BigInt(s_blind) * k_inv) % admin_N
}

export function verifySignature(signature, admin_e, admin_N, m_int) {
  return modPow(signature, admin_e, admin_N) === (m_int % admin_N)
}

export function encryptChoice(choiceIdx, counter_e, counter_N) {
  const encodedChoice = BigInt(choiceIdx + 1)
  return modPow(encodedChoice, counter_e, counter_N)
}

export function formatCode(value) {
  const v = value.replace(/\s/g, '').toUpperCase()
  let out = ''
  for (let i = 0; i < v.length && i < 12; i++) {
    if (i && i % 4 === 0) out += ' '
    out += v[i]
  }
  return out
}

export function encryptVote(choiceIndex, N2, counter_e, counter_N) {
  const n2Clean = N2.toUpperCase().replace(/\s/g, '')
  
  // pack: 2 bytes (vote index) + 12 bytes (N2 ASCII) = 14 bytes
  const combined = new Uint8Array(14)
  combined[0] = (choiceIndex >> 8) & 0xff
  combined[1] =  choiceIndex       & 0xff
  for (let i = 0; i < 12; i++) {
    combined[2 + i] = n2Clean.charCodeAt(i)
  }

  // convert to BigInt and RSA encrypt: c = m^e mod N
  const m = BigInt(
    '0x' + Array.from(combined)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')
  )
  return modPow(m, counter_e, counter_N)
}