class Account:
    balance = {'total_balance':0, 'available_balance':0, 'positions':{}}

    def get_balance(self) -> dict:
        """
        Get the balance for all symbols.

        :return: The balance for all symbols.
        """
        return self.balance
    
    def get_total_balance(self) -> float:
        """
        Get the total balance.

        :return: The total balance.
        """
        return self.balance['total_balance']
    
    def get_available_balance(self) -> float:
        """
        Get the available balance.

        :return: The available balance.
        """
        return self.balance['available_balance']
    
    def get_open_position(self) -> dict:
        """
        Get the open position.

        :return: The open position.
        """
        return self.balance['positions']
    
    def get_open_symbols(self) -> list:
        """
        Get the open symbols.

        :return: The open symbols.
        """
        return list(self.balance['positions'].keys())