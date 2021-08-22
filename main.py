from datetime import datetime, timedelta
import numpy as np
import math
from functools import reduce
import json
import argparse


# Instrument class that gathers data from the FIRE regulated json file
class Instrument:

    def __init__(self, data):
        self.id = data['id']
        self.type = data['type']
        self.date = datetime.strptime(data['date'], '%Y-%m-%dT%H:%M:%SZ')
        self.start_date = datetime.strptime(data['start_date'], '%Y-%m-%dT%H:%M:%SZ')
        self.end_date = datetime.strptime(data['end_date'], '%Y-%m-%dT%H:%M:%SZ')
        self.trade_date = datetime.strptime(data['trade_date'], '%Y-%m-%dT%H:%M:%SZ')
        self.currency_code = data['currency_code']
        self.customer_type = data["customer"]['type']
        self.issuer_type = None
        self.sft_type = data['sft_type']
        self.mtm_dirty = None
        self.movement = data['movement']
        self.balance = None

        self.time_to_maturity = (self.end_date - self.start_date).days / 365

        if self.id == "rev_repo_asset_leg":
            self.mtm_dirty = data['mtm_dirty']
            self.issuer_type = data["issuer"]['type']
        else:
            self.balance = data['balance']


# Main K-TCD class, this is where the actual evaluaton is done.
class K_TCD:

    def __init__(self, asset_leg, cash_leg):
        self.asset_leg = asset_leg
        self.cash_leg = cash_leg
        self.alpha = 1.2
        self.exposure_value = None
        self.risk_factor = None
        self.credit_valuation_adjustment = None
        self.value = None

        self.effective_notional = None
        self.supervisory_factor = None

    # Initialises set, splitting trades by currency in order to evaluate notionalAmounts separately
    def initialize(self):
        self.exposure_value = self.get_exposure_value()
        self.risk_factor = self.get_risk_factor()
        self.credit_valuation_adjustment = self.get_credit_valuation_adjustment()

    def get_replacement_cost(self):
        # Article 28c: Replacement Cost
        # For repurchase transactions and securities or commodities lending or borrowing transactions, RC is determined as the 
        # amount of cash lent or borrowed; cash lent by the investment firm is to be treated as a positive amount and cash 
        # borrowed by the investment firm is to be treated as a negative amount; 

        return float(self.asset_leg.mtm_dirty)
    
    def get_notional_amount(self):
        return float(self.cash_leg.balance)

    def get_duration(self):
        duration = 1.

        if "bond" not in self.asset_leg.type or "index" not in self.asset_leg.type:
            duration = (1 - math.exp(-.05 * self.asset_leg.time_to_maturity)) / .05

        return duration

    def get_supervisory_delta(self):
        # Transactions other than options and swaptions have supervisory delta
        # equal to 1 as specified in Article 29 (6).

        return 1.

    def get_effective_notional(self):
        notional_amount = self.get_notional_amount()
        duration = self.get_duration()
        supervisory_delta = self.get_supervisory_delta()

        return  notional_amount * duration * supervisory_delta

    def get_supervisory_factor(self):
        if "swap" in self.asset_leg.type:
            return .005
        elif "fx" in self.asset_leg.type:
            return .04
        elif "bond" in self.asset_leg.type:
            return .01
        elif "index" in self.asset_leg.type:
            return .2
        elif "commodity" in self.asset_leg.type:
            return .18
        else:
            return .32


    def get_potential_future_exposure(self):
        # See Article 29: Potential Future Exposure
        self.effective_notional = self.get_effective_notional()
        self.supervisory_factor = self.get_supervisory_factor()

        return self.effective_notional * self.supervisory_factor

    def get_collateral(self):
        return abs(self.cash_leg.balance + self.asset_leg.mtm_dirty) * .00707

    def get_exposure_value(self):
        replacement_cost = self.get_replacement_cost()
        potential_future_exposure = self.get_potential_future_exposure()
        collateral = self.get_collateral()

        return max(0, replacement_cost + potential_future_exposure - collateral) 

    def get_risk_factor(self):
        if "govt" in [self.asset_leg.customer_type, self.cash_leg.customer_type] or "bond" in [self.asset_leg.customer_type, self.cash_leg.customer_type]:
            return .016
        else:
            return .08

    def get_credit_valuation_adjustment(self):
        return 1.                                   # SFTs have CVA equal to 1 as specified in Article 32 d.



    # Main method that calculates K_TCD for the instruments. Initialises exposure,
    # gets risk factor value and credit valuation adjustment. Then returns the K_TCD.
    def calculate_K_TCD(self):
        self.value =  self.alpha * self.exposure_value * self.risk_factor * self.credit_valuation_adjustment

        return self.value


def main():

    # argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', default='data', nargs='?',
                        help='Name of the JSON file to load (it will need to be stored in "examples/")')
    args = parser.parse_args()

    # Set up. Opens JSON file (data.json by default) and initializes the process with instruments.
    with open("examples/{}.json".format(args.file), 'r') as f:
        data = json.load(f)
    instruments = [Instrument(item) for item in data['data']]
    cash_leg = Instrument(data["data"][0])
    asset_leg = Instrument(data["data"][1])

    process = K_TCD(asset_leg, cash_leg)
    process.initialize()

    print(
        process.calculate_K_TCD()
    )

    return process.value

if __name__ == "__main__":
    main()
