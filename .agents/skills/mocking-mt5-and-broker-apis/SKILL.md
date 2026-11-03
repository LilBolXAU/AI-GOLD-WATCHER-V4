---
name: mocking-mt5-and-broker-apis
description: >-
  Provides mock adapters and test fixtures for MetaTrader 5, enabling automated testing
  of data feeds, connection loss, trade execution, and error handling without a live terminal.
license: Apache-2.0
metadata:
  domain: algorithmic-trading
  subdomain: software-testing
  tags: testing, mocking, mt5, unit-test, integration-test, fixtures
  version: "1.0.0"
---

# Mocking MetaTrader 5 & Broker APIs

This skill provides testing patterns and mock implementations of the `MetaTrader5` Python package, ensuring 100% test coverage of all edge cases without requiring an active MT5 terminal or real broker connection.

## Why Mock MT5?
1. **Host Independence**: The official `MetaTrader5` package only runs on Windows x86-64 with an active MT5 installation. Mocks allow headless CI runs anywhere.
2. **Deterministic Edge Cases**: Simulating network timeouts, broker requotes (`10004`), server disconnects, and partial fills (`10010`) cannot be reliably triggered on live demo servers on command.
3. **Safety Assurance**: Guarantees that automated test suites never accidentally place live orders.

## Architecture of the MT5 Terminal Adapter

The core rule: **Never call `import MetaTrader5` directly in business logic.**
Always interact with an abstract `MT5TerminalAdapter` protocol.

```python
from typing import Protocol, Optional, Sequence
import numpy as np

class MT5TerminalAdapter(Protocol):
    def initialize(self, path: Optional[str] = None) -> bool: ...
    def shutdown(self) -> None: ...
    def terminal_info(self) -> Optional[object]: ...
    def account_info(self) -> Optional[object]: ...
    def symbol_info(self, symbol: str) -> Optional[object]: ...
    def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int) -> Optional[np.ndarray]: ...
    def order_send(self, request: dict) -> Optional[object]: ...
```

## Mock Implementation Pattern

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np

@dataclass
class MockSymbolInfo:
    name: str = "XAUUSDm"
    digits: int = 2
    point: float = 0.01
    volume_min: float = 0.01
    volume_max: float = 200.0
    volume_step: float = 0.01
    trade_stops_level: int = 0
    trade_contract_size: float = 100.0
    filling_mode: int = 1  # SYMBOL_FILLING_FOK

@dataclass
class MockTradeResult:
    retcode: int = 10009  # TRADE_RETCODE_DONE
    deal: int = 123456
    order: int = 654321
    volume: float = 0.01
    price: float = 2650.50
    comment: str = "Mock Fill"

class MockMT5Adapter:
    def __init__(self, connected: bool = True, default_retcode: int = 10009):
        self.connected = connected
        self.default_retcode = default_retcode
        self.orders_sent = []
        
    def initialize(self, path: Optional[str] = None) -> bool:
        return self.connected
        
    def shutdown(self) -> None:
        self.connected = False
        
    def symbol_info(self, symbol: str) -> Optional[MockSymbolInfo]:
        if not self.connected:
            return None
        if symbol == "XAUUSDm":
            return MockSymbolInfo()
        return None
        
    def order_send(self, request: Dict[str, Any]) -> MockTradeResult:
        if not self.connected:
            return None
        self.orders_sent.append(request)
        return MockTradeResult(
            retcode=self.default_retcode,
            volume=request.get("volume", 0.01),
            price=request.get("price", 2650.0)
        )
```

## Mandatory Test Cases to Cover

1. `symbol_info` returning `None` (symbol not selected or disconnected).
2. `order_send` returning `retcode = 10004` (Requote): verifies retry budget and rejection.
3. `order_send` returning `retcode = 10027` (Client disables AT): raises actionable error.
4. `order_send` returning `retcode = 10010` (Partial Fill): verifies residual volume handling.
5. `order_send` returning `None` or raising: marks trade as ambiguous, initiates magic number reconciliation.
