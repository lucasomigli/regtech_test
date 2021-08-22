from main import *
import pytest

# Tests are parametrised using files stored in 'examples/'

@pytest.fixture(params=['data', 'data1', 'data2'])
def testCase(request):
    with open("examples/{}.json".format(request.param), 'r') as f:
        data = json.load(f)
    repo_legs = [Instrument(item) for item in data['data']]
    cash_leg = Instrument(data["data"][0])
    asset_leg = Instrument(data["data"][1])
    process = K_TCD(asset_leg, cash_leg)
    return {
        "data": data,
        "repo_legs": [cash_leg, asset_leg],
        "process": process
    }


def testJson(testCase):
    assert testCase['data']['name'] == 'Rev Repo Data'
    assert testCase['data']['data'] != None
    assert len([x for x in testCase['data']['data']]) > 1


def testTypes(testCase):

    for instrument in testCase['repo_legs']:
        assert type(instrument) == Instrument
        assert type(instrument.time_to_maturity) == float

    testCase['process'].initialize()
    testCase['process'].calculate_K_TCD()

    assert type(testCase['process']) == K_TCD
    assert type(testCase['process'].get_replacement_cost()) == float
    assert type(testCase['process'].get_notional_amount()) == float
    assert type(testCase['process'].get_duration()) == float
    assert type(testCase['process'].get_supervisory_delta()) == float
    assert type(testCase['process'].get_supervisory_factor()) == float
    assert type(testCase['process'].get_potential_future_exposure()) == float
    assert type(testCase['process'].get_collateral()) == float
    assert type(testCase['process'].get_exposure_value()) == float
    assert type(testCase['process'].get_risk_factor()) == float
    assert type(testCase['process'].get_credit_valuation_adjustment()) == float