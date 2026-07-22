"""MCPClient — client générique pour serveurs MCP (Model Context Protocol).

Sert de façade unifiée aux serveurs MCP des différentes plateformes
(ex : MCP Server Reddit connecté en Phase 0, MCP LinkedIn en Phase 1).
Le transport concret (stdio / HTTP) reste à brancher (TODO).
"""

from __future__ import annotations

from typing import Any


class MCPClient:
    """Client MCP minimal — façade `call_tool` vers un serveur MCP."""

    def __init__(self, server_name: str, config: dict[str, Any] | None = None) -> None:
        self.server_name = server_name
        self.config = config or {}
        self._session = None

    def connect(self) -> None:
        """Établit la session avec le serveur MCP."""
        # TODO: instancier le transport MCP (stdio/HTTP) et ouvrir la session.
        raise NotImplementedError(
            "MCPClient.connect() : transport MCP à brancher (Phase 1)."
        )

    def call_tool(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Appelle un outil exposé par le serveur MCP."""
        # TODO: sérialiser la requête MCP et renvoyer le résultat.
        raise NotImplementedError(
            f"MCPClient.call_tool({tool!r}) non implémenté (Phase 1)."
        )

    def close(self) -> None:
        """Ferme la session MCP."""
        self._session = None
