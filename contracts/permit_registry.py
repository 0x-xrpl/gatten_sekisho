from boa3.builtin import public, atoi
from boa3.builtin.storage import get, put


@public
def register_permit(permit_id: str, decision_hash: bytes, issued_at: int, expires_at: int, policy_version: str) -> bool:
    record = (
        decision_hash
        + b"|"
        + policy_version.encode()
        + b"|"
        + str(issued_at).encode()
        + b"|"
        + str(expires_at).encode()
    )
    put(permit_id, record)
    return True


@public
def get_permit(permit_id: str) -> bytes:
    return get(permit_id)


@public
def is_valid(permit_id: str, decision_hash: bytes, now: int) -> bool:
    record = get(permit_id)
    if len(record) == 0:
        return False
    data = record.split(b"|")
    if len(data) < 4:
        return False
    stored_hash = data[0]
    expires = atoi(data[3])
    return stored_hash == decision_hash and now <= expires
