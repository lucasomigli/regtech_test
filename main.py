from datetime import datetime
import math
import json
import argparse


asset_classes ={
    "abs": "CR",
    "abs_auto": "CR",
    "abs_consumer": "CR",
    "abs_other": "CR",
    "abs_sme": "CR",
    "acceptance": "other",
    "bill_of_exchange": "other",
    "bond": "CR",
    "cash": "other",
    "cash_ratio_deposit": "other",
    "cb_facility": "other",
    "cb_reserve": "other",
    "cd": "other",
    "cmbs": "CR",
    "commercial_paper": "other",
    "convertible_bond": "CR",
    "covered_bond": "CR",
    "debt": "CR",
    "emtn": "CR",
    "equity": "EQ",
    "financial_guarantee": "CR",
    "financial_sloc": "CR",
    "frn": "other",
    "guarantee": "CR",
    "index": "CR",
    "index_linked": "CR",
    "letter_of_credit": "CR",
    "mbs": "CR",
    "mtn": "CR",
    "other": "other",
    "performance_bond": "CR",
    "performance_guarantee": "CR",
    "performance_sloc": "CR",
    "pref_share": "EQ",
    "rmbs": "CR",
    "rmbs_trans": "CR",
    "share": "EQ",
    "share_agg": "EQ",
    "spv_mortgages": "CR",
    "spv_other": "other",
    "struct_note": "other",
    "treasury": "IR",
    "urp": "CR",
    "warranty": "CR"
}

factor = dict(
            IR=.005,
            FX=.04,
            CR=.01,
            EQ_sigle=.32,   
            EQ_index=.20, 
            Commodity=18, 
            other=.32
            )

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

        if "CR" == factor[asset_classes[self.asset_leg.type]] or "IR" == factor[asset_classes[self.asset_leg.type]]:
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

        return factor[asset_classes[self.asset_leg.type]]

    def get_potential_future_exposure(self):
        # See Article 29: Potential Future Exposure
        self.effective_notional = self.get_effective_notional()
        self.supervisory_factor = self.get_supervisory_factor()

        return self.effective_notional * self.supervisory_factor

    def get_collateral(self):
        # Article 30 (2b):
        # The value of collateral for repurchase agreements is determined as the sum of the CMV of the security leg
        # and the net amount of collateral posted or received by the investment firm. 
        volatility_adjustment = .00707
        if 1 < self.asset_leg.time_to_maturity <= 5:
            volatility_adjustment = .02121
        else:
            volatility_adjustment = .04243

        return (self.asset_leg.mtm_dirty + self.cash_leg.balance) * volatility_adjustment

    def get_exposure_value(self):
        replacement_cost = self.get_replacement_cost()
        potential_future_exposure = self.get_potential_future_exposure()
        collateral = self.get_collateral()

        return max(0., replacement_cost + potential_future_exposure - collateral) 

    def get_risk_factor(self):
        if "govt" in self.asset_leg.issuer_type or "government" in self.asset_leg.issuer_type:
            return .016
        else:
            return .08

    def get_credit_valuation_adjustment(self):
        # SFTs have CVA equal to 1 as specified in Article 32 d.
        return 1.



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
