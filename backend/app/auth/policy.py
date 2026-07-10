"""Casbin policy enforcement."""
import casbin
import os
from pathlib import Path

# Get the directory where this file is located
BASE_DIR = Path(__file__).parent.parent.parent

# Initialize Casbin enforcer
model_path = BASE_DIR / "casbin" / "model.conf"
policy_path = BASE_DIR / "casbin" / "policy.csv"

if not model_path.exists() or not policy_path.exists():
    raise FileNotFoundError(f"Casbin config files not found: {model_path}, {policy_path}")

enforcer = casbin.Enforcer(str(model_path), str(policy_path))

def can_execute(user_id: str, device_id: str, command: str) -> bool:
    """Check if a user can execute a command on a device."""
    # Convert device_id to pattern if needed
    # e.g., "device-123" matches "device_*" pattern
    result = enforcer.enforce(user_id, device_id, command)
    return result

def add_policy(user_id: str, device_id: str, command: str) -> bool:
    """Add a new policy rule."""
    return enforcer.add_policy(user_id, device_id, command)

def remove_policy(user_id: str, device_id: str, command: str) -> bool:
    """Remove a policy rule."""
    return enforcer.remove_policy(user_id, device_id, command)

def get_policies() -> list:
    """Get all policy rules."""
    return enforcer.get_policy()

def load_policy() -> None:
    """Reload policies from file."""
    enforcer.load_policy()
