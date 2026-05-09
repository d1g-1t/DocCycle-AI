"""Render context builder — prepares template variables for rendering."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

log = structlog.get_logger(__name__)


class RenderContextBuilder:
    """Build a render context from contract data + user-supplied variables.

    Merges system variables (dates, IDs, formatting helpers) with
    user-supplied template variables to produce a complete context
    for the Jinja2 renderer.
    """

    def build(
        self,
        user_variables: dict[str, Any],
        contract_title: str = "",
        contract_type: str = "",
        counterparty_name: str | None = None,
        amount: Decimal | None = None,
        currency: str | None = None,
        jurisdiction: str | None = None,
    ) -> dict[str, Any]:
        """Merge system and user variables into a single render context."""
        now = datetime.now(UTC)

        system_vars: dict[str, Any] = {
            # Dates
            "current_date": now.strftime("%d.%m.%Y"),
            "current_date_iso": now.date().isoformat(),
            "current_year": str(now.year),

            # Contract metadata
            "contract_title": contract_title,
            "contract_type": contract_type,
            "counterparty_name": counterparty_name or "_______________",
            "jurisdiction": jurisdiction or "Российская Федерация",

            # Financial
            "amount": self._format_amount(amount),
            "amount_raw": str(amount) if amount else "",
            "currency": currency or "RUB",
            "currency_symbol": self._currency_symbol(currency),

            # Formatting helpers
            "nbsp": "\u00A0",
            "mdash": "\u2014",
        }

        # User variables override system defaults
        context = {**system_vars, **user_variables}
        log.debug(
            "render_context.built",
            system_keys=len(system_vars),
            user_keys=len(user_variables),
        )
        return context

    @staticmethod
    def _format_amount(amount: Decimal | None) -> str:
        """Format monetary amount with Russian locale conventions."""
        if amount is None:
            return "_______________"
        # Format with thousand separators and 2 decimal places
        formatted = f"{amount:,.2f}"
        # Russian convention: space as thousands separator, comma as decimal
        formatted = formatted.replace(",", " ").replace(".", ",")
        return formatted

    @staticmethod
    def _currency_symbol(currency: str | None) -> str:
        """Map ISO 4217 code to symbol."""
        symbols = {
            "RUB": "₽",
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "CNY": "¥",
        }
        return symbols.get(currency or "RUB", currency or "₽")
