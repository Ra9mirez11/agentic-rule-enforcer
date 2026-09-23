# Project Agent Rules

Engineering guidelines and safety boundaries for developers and AI coding agents.

## Section 1: Security & Secrets
Strict boundaries against committing sensitive credentials or private keys.

### RULE-01-SECRETS: Hardcoded Secrets and Tokens
- Severity: CRITICAL
- Description: Detects hardcoded API keys, private keys, passwords, and tokens.
- FileTypes: *
- Pattern: `(?i)(?:api_key|apikey|secret_key|private_key|auth_token|bearer_token|password)\s*=\s*['"][a-zA-Z0-9_\-]{16,}['"]`
- Fix: env_var
- Message: Replace hardcoded credential with environment variable lookup (e.g., os.environ or process.env).

### RULE-02-ETH-KEY: Private Key Hex Constants
- Severity: CRITICAL
- Description: Detects raw 32-byte hexadecimal private keys.
- FileTypes: .py, .ts, .js, .sol, .env
- Pattern: `0x[a-fA-F0-9]{64}`
- Fix: env_var
- Message: Do not hardcode Ethereum/ECDSA private keys in repository files.

## Section 2: Agent Cleanliness & Log Fluff
Ensures code is clean and free of debug statements or unhandled placeholder patterns.

### RULE-03-FLUFF: Debug and Console Dumps
- Severity: HIGH
- Description: Detects forbidden debug logging statements.
- FileTypes: .py, .js, .ts
- Pattern: `(?i)(?:console\.log\(|print\(.*\b(?:TODO_DEBUG|DEBUG_LOG|DUMP_OUTPUT)\b)`
- Fix: remove
- Message: Remove debug print/console statements before finalizing commits.

### RULE-04-PASS-TODO: Silent Error Swallowing
- Severity: MEDIUM
- Description: Detects bare pass blocks in except handlers.
- FileTypes: .py
- Pattern: `except\s+Exception:\s*pass`
- Fix: manual
- Message: Do not silently swallow exceptions; implement proper error handling or logging.

## Section 3: Scope Guard
Protects project configuration and core policies from unauthorized agent drift.

### RULE-05-PROTECTED-SCOPE: Unauthorized Edits to Root Secrets
- Severity: HIGH
- Description: Prevents creation or modification of tracked local secret files.
- FileTypes: .env, .env.local, .env.production
- Pattern: `^.*$`
- Fix: manual
- Message: Local environment secret files must remain gitignored and untracked.
