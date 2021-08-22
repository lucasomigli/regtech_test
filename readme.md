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
        get_replacement_cost()              # 
        get_notional_amount()               # 
        get_duration()                      # 
        get_supervisory_delta()             # 
        get_effective_notional()            #
        get_supervisory_factor()            #
        get_potential_future_exposure()     #
        get_collateral()                    #
        get_exposure_value()                #
        get_risk_factor()                   #
        get_credit_valuation_adjustment()   #

The K_TCD class will then take the instantiated Instruments and computes the necessary calculations abd store the result in self.value. 
It calculates:
- α = 1,2; 
- EV = the exposure value calculated in accordance with Article 27; 
- RF = the risk factor defined per counterparty type as set out in Table 2;  
- CVA = the credit valuation adjustment calculated in accordance with Article 32 

Then computes the formula for the requirement of the funds under K-TCD: α • EV • RF • CVA.