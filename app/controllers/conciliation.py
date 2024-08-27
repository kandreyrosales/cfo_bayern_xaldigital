from collections import defaultdict
from decimal import Decimal
from typing import Dict
from sqlalchemy import Tuple
from datetime import datetime
from app.models import get_conciliations_view_data, get_eips_iva_conciliations_view_data


class ConciliationController:

    @classmethod
    def get_conciliations_view_data(
        cls,
        calendar_filter_start_date: datetime,
        calendar_filter_end_date: datetime,
        rfc_selector: str,
        customer_name_selector: str,
    ) -> Tuple:

        result, totals, sum_by_rfc = get_conciliations_view_data(
            calendar_filter_start_date=calendar_filter_start_date,
            calendar_filter_end_date=calendar_filter_end_date,
            rfc_selector=rfc_selector,
            customer_name_selector=customer_name_selector,
        )

        column_names = result.keys()
        data_result = [dict(zip(column_names, row)) for row in result]

        rcf_column_names = sum_by_rfc.keys()
        sum_rfc_data = [dict(zip(rcf_column_names, row)) for row in sum_by_rfc]

        column_names_totals = totals.keys()
        data_totals = [dict(zip(column_names_totals, row)) for row in totals]

        return data_result, data_totals, sum_rfc_data

    @classmethod
    def get_eips_iva_conciliations_view_data(
        cls,
        calendar_filter_start_date: datetime,
        calendar_filter_end_date: datetime,
        rfc_selector: str,
        customer_name_selector: str,
    ) -> Tuple:

        iva_ieps, total_income = get_eips_iva_conciliations_view_data(
            calendar_filter_start_date=calendar_filter_start_date,
            calendar_filter_end_date=calendar_filter_end_date,
            rfc_selector=rfc_selector,
            customer_name_selector=customer_name_selector,
        )

        column_names = iva_ieps.keys()
        tax_data = [dict(zip(column_names, row)) for row in iva_ieps]

        return tax_data, total_income

    @classmethod
    def filter_bank_transactions(cls, rfcs, transactions):
        match_transactions = []
        for item in rfcs:
            result = list(
                filter(
                    lambda transaction: int(transaction[3]) == int(item["sum"]),
                    transactions,
                )
            )
            if len(result) > 0:
                bank = result[0]
                item["bank_name"] = bank[0]
                item["comment"] = bank[1]
                item["value_date"] = bank[2]
                item["posting_amount"] = bank[3]
                item["ref"] = bank[4]
                match_transactions.append(item)

        return match_transactions

    @classmethod
    def update_bank_info(cls, item, bank_info_list) -> Dict:
        for bank_info in bank_info_list:
            if item["clearing_payment_policy"] == bank_info["clearing_payment_policy"]:
                item["bank_name"] = bank_info["bank_name"]
                item["bank_ref"] = bank_info["ref"]
                item["value_date"] = bank_info["value_date"].strftime("%d/%m/%Y")
                item["posting_amount_number"] = bank_info["posting_amount"]
                item["posting_amount"] = f"${bank_info['posting_amount']:,.2f}"
                item["comment"] = bank_info["comment"]
                break
        return item

    @classmethod
    def group_transactions(cls, transactions):
        grouped_data = defaultdict(
            lambda: {
                "bank_name": "",
                "total_posting_amount": Decimal("0.00"),
                "total_transactions": 0,
            }
        )

        for transaction in transactions:
            bank_name = transaction["bank_name"]
            grouped_data[bank_name]["bank_name"] = bank_name
            grouped_data[bank_name]["total_posting_amount"] += transaction[
                "posting_amount"
            ]
            grouped_data[bank_name]["total_transactions"] += 1

        grouped_dict = dict(grouped_data)

        return list(
            map(
                lambda x: {
                    "bank_name": x["bank_name"],
                    "total_posting_amount": x["total_posting_amount"],
                    "total_transactions": x["total_transactions"],
                },
                grouped_dict.values(),
            )
        )
