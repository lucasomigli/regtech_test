from datetime import datetime, timedelta
import numpy as np
from functools import reduce
import json
import argparse
from terminaltables import AsciiTable


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
        self.issuer_type = data["issuer"]['type']
        self.sft_type = data['sft_type']
        self.mtm_dirty = data['mtm_dirty']
        self.movement = data['movement']
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

        return self.cash_leg.balance

    def get_potential_future_exposure(self):
        # See Article 29: Potential Future Exposure
        pass

    def get_collateral(self):
        pass

    def get_exposure_value(self):
        replacement_cost = self.get_replacement_cost()
        potential_future_exposure = selg.get_potential_future_exposure()
        collateral = self.get_collateral()

        return max(0, replacement_cost + potential_future_exposure – collateral) 

    def get_risk_factor(self):
        if ["govt", "government"] in self.asset_leg.customer_type or ["govt", "government"] in self.asset_leg.issuer_type:
            return .016
        else:
            return .08

    def get_credit_valuation_adjustment(self):
        return 1        # SFTs have CVA equal to 1 as specified in Article 32 d.



    # Main method that calculates K_TCD for the instruments. Initialises exposure,
    # gets risk factor value and credit valuation adjustment. Then returns the K_TCD.
    def calculate(self):
        self.initialize()

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
    process = SA_CCR(instruments)
    process.ead = process.getEAD()

    # Using terminaltables for drwawing tables.
    INSTRUMENTS_TABLE = [['Instrument', 'Type', 'Maturity (years)', 'Notional', 'Pay Leg', 'Receive Leg', 'Market Value', 'Adjusted Notional', 'Delta']]
    INSTRUMENTS_TABLE.extend([[i.id, i.type, i.maturity, i.notional_amount, i.payment_type,
                               i.receive_type, i.mtm_dirty, i.getAdjustedNotional(), i.delta]for i in instruments])

    SA_CCR_TABLE = [['Replacement Cost', 'Effective Notionals', 'AddOn', 'EAD'],
                    [process.getReplacementCost(), "Set1: %f; Set2: %f" % tuple(process.effectiveNotionals), process.getAddOn(), process.ead]]

    print(AsciiTable(INSTRUMENTS_TABLE, 'INSTRUMENTS').table, '\n',
          AsciiTable(SA_CCR_TABLE, 'FINALISED EAD').table)

    return process.EAD


if __name__ == "__main__":
    main()
