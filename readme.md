## Table of Contents

* [Usage](#usage)
* [How It Works](#usage)

## Usage
Download repo and save locally. To load a JSON file run 

    python main.py 

or

    python main.py data

There are a total of 3 JSON test files included in the 'examples' folder

For tests, either run pytest in root or use run_tests.sh

## How It Works
There are a total of two main classes:

    class Instrument:
        pass
The Instrument Class will load the JSON files and store values in a class object. This will serve the main process K_TCD.

    class K_TCD(asset_leg, cash_leg):
        initialize()                        # Initializes the class and loads both legs of the reverse repo and gets EV, RF and CVA. 
        get_replacement_cost()              # calculates the replacement cost from the two legs
        get_notional_amount()               # gets the notional amount as float. In a reverse repo this is the asset leg balance  
        get_duration()                      # duration is stated as (1 - e^(-.05 * maturity) ) / .05 for credit and interest rate derivatives.
        get_supervisory_delta()             # returns 1.0 as it is the default value for repo agreements
        get_effective_notional()            # calculates the EN as notional * duration * supervisory delta
        get_supervisory_factor()            # gets the relative superisory factor according to institution and time for settlement
        get_potential_future_exposure()     # calculated as effective_notional * supervisory_factor
        get_collateral()                    # Calculates the volatility adjustments as specified in the DOCS.
        get_exposure_value()                # Max(0; replacement cost + potential future exposure – collateral)
        get_risk_factor()                   # returns .016 for governmental issuers and .08 for all other cases.
        get_credit_valuation_adjustment()   # SFTs have CVA equal to 1.0 as specified in Article 32 d.

The K_TCD class will then take the instantiated Instruments and computes the necessary calculations abd store the result in self.value. 
It calculates:
- α = 1,2; 
- EV = the exposure value calculated in accordance with Article 27; 
- RF = the risk factor defined per counterparty type as set out in Table 2;  
- CVA = the credit valuation adjustment calculated in accordance with Article 32 

Then computes the formula for the requirement of the funds under K-TCD: α • EV • RF • CVA.