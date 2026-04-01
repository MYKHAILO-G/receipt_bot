from abc import ABC, abstractmethod


class Database(ABC):
    """
    Abstract base class defining the contract for all database backends.
    Implement this class to add a new storage backend (SQLite, PostgreSQL, etc.)
    and swap it in via dependency injection.
    """

    # ------------------------------------------------------------------
    # User metadata
    # ------------------------------------------------------------------

    @abstractmethod
    def save_user(self, user_id: int | str, user_data: dict) -> None:
        """
        Persist arbitrary user metadata (name, username, etc.).

        Args:
            user_id:   Unique identifier for the user.
            user_data: Dict of metadata to store (e.g. {"name": "Alice"}).
        """

    @abstractmethod
    def get_user(self, user_id: int | str) -> dict | None:
        """
        Retrieve user metadata.

        Returns:
            The stored metadata dict, or None if the user does not exist.
        """

    # ------------------------------------------------------------------
    # Receipt data
    # ------------------------------------------------------------------

    @abstractmethod
    def save_receipt(self, user_id: int | str, receipt: dict) -> None:
        """
        Persist a receipt and its line items for a user.

        Expected receipt format::

            {
                "date":  "2024-01-01",
                "store": "Silpo",
                "items": [
                    {"name": "Milk",  "price": 45.0},
                    {"name": "Bread", "price": 30.0},
                ]
            }

        Args:
            user_id: Unique identifier for the user.
            receipt: Receipt dict as described above.
        """

    @abstractmethod
    def get_receipts(self, user_id: int | str) -> list[dict] | None:
        """
        Retrieve all receipt rows for a user.

        Returns:
            A list of row dicts with keys matching the storage headers
            (UUID, Date, Store, Item, Price), an empty list if the user
            exists but has no data, or None if the user has no storage at all.
        """

    @abstractmethod
    def get_xlsx_path(self, user_id: int | str) -> str | None:
        """
        Return the absolute path to an Excel export of the user's data,
        or None if unavailable.

        Backends that do not use Excel files natively should either:
          - generate a temporary .xlsx on demand and return its path, or
          - return None to signal that file export is unsupported.
        """