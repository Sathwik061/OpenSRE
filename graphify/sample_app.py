"""
sample_app.py — Demo Application with Graphify Auto-Error Detection
====================================================================
This shows the COMPLETE auto-detection flow working:

  Real app error → GraphifyHook catches it → Sentinel RCA → Terminal

Run it:
    python sample_app.py

You'll see:
  1. App starts normally
  2. A simulated error occurs (e.g. DB connection refused)
  3. Graphify catches it automatically
  4. RCA investigation starts
  5. Root cause appears in terminal
"""
import sys
import time
import random
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── 2 lines to install the hook ───────────────────────────────────────────────
from error_hook import GraphifyHook
GraphifyHook.install(service="payment-service", environment="development")
# ─────────────────────────────────────────────────────────────────────────────


# ── Simulated services ────────────────────────────────────────────────────────

class Database:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._connected = False

    def connect(self):
        # Simulate a random DB failure
        if random.random() < 0.7:   # 70% chance of failure (for demo)
            raise ConnectionRefusedError(
                f"Connection refused to {self.host}:{self.port} — "
                "database is restarting"
            )
        self._connected = True

    def query(self, sql: str):
        if not self._connected:
            raise RuntimeError("Cannot query: no database connection")
        return {"rows": [], "status": "ok"}


class PaymentService:
    def __init__(self):
        self.db = Database("postgres", 5432)

    def process_payment(self, amount: float, user_id: str):
        self.db.connect()   # This may raise ConnectionRefusedError
        result = self.db.query(f"INSERT INTO payments VALUES ({amount}, '{user_id}')")
        return result


# ── Main app logic ────────────────────────────────────────────────────────────

def main():
    border = "=" * 60
    print(f"\n{border}")
    print("  SAMPLE APP  --  Payment Service (with Graphify Hook)")
    print(border)
    print("  The app will run, hit an error, and auto-trigger RCA.\n")

    service = PaymentService()

    print("  [App] Processing payment requests...\n")

    for i in range(1, 4):
        print(f"  [App] Request #{i}: Processing payment of $99.99 for user-{i:03d}...")
        time.sleep(1)

        try:
            service.process_payment(99.99, f"user-{i:03d}")
            print(f"  [App] Request #{i}: Payment processed OK\n")
        except ConnectionRefusedError as e:
            # Option 1: Let it propagate → GraphifyHook catches it automatically
            print(f"  [App] Request #{i}: FAILED — {e}\n")
            print("  [App] Unhandled exception — Graphify hook will auto-trigger RCA...\n")
            raise   # <-- GraphifyHook.install() catches this automatically
        except Exception as e:
            # Option 2: Caught exception — trigger manually
            GraphifyHook.trigger_manual(
                error_type=type(e).__name__,
                error_message=str(e),
                service="payment-service",
            )


if __name__ == "__main__":
    main()
