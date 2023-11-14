class Account:
    balance = {}

    def get_balance(self) -> dict:
        """
        Get the balance for all symbols.

        :return: The balance for all symbols.
        """
        return self.balance