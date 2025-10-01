    @staticmethod
    def get_date_range(selected_period):
        """
        Zwraca zakres dat dla IMAP w zależności od wybranego okresu
        Args:
            selected_period (str): np. "last_week", "last_month", "today"
        Returns:
            tuple(datetime, datetime): (date_from, date_to)
        """
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        if selected_period == "last_week":
            date_from = now - timedelta(days=7)
            date_to = now
        elif selected_period == "last_month":
            date_from = now - timedelta(days=30)
            date_to = now
        elif selected_period == "today":
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_to = now
        else:
            date_from = None
            date_to = now
        return (date_from, date_to)