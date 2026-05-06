import secrets
import string

CHARSET = string.ascii_uppercase + string.digits

def generate_code(length=12) -> str:
    return ''.join(secrets.choice(CHARSET) for _ in range(length))

def format_code(code: str) -> str:
    return ' '.join(code[i:i+4] for i in range(0, len(code), 4))

def generate_n1_codes(num_voters: int) -> dict:
    codes = {}
    generated = set()
    for voter_id in range(1, num_voters + 1):
        while True:
            code = generate_code(12)
            if code not in generated:
                generated.add(code)
                codes[voter_id] = code
                break
    print(f"[N1 Handler] Generated {num_voters} unique N1 codes.")
    return codes

def generate_room_code() -> str:
    code = generate_code(12)
    print(f"[N1 Handler] Room code: {format_code(code)}")
    return code

if __name__ == "__main__":
    n1_codes = generate_n1_codes(5)
    for voter_id, code in n1_codes.items():
        print(f"  Voter {voter_id}: {format_code(code)}")
    generate_room_code()
