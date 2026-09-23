"""Example service module with typical AI coding agent violations."""

import os


def authenticate_user():
    # RULE-01-SECRETS: Hardcoded API secret
    api_key = "mock_secret_agent_key_998877665544332211"
    return api_key


def fetch_blockchain_data():
    # RULE-02-ETH-KEY: Raw private key hex
    private_key = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
    # RULE-03-FLUFF: Debug dump print
    print("TODO_DEBUG fetch_blockchain_data response:", private_key)
    return {"status": "ok"}
