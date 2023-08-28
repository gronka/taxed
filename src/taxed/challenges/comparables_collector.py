from datetime import datetime
import requests
from sqlalchemy.orm import Session
import traceback
from typing import List
import uuid

from taxed.core import db_commit, plog, ResponseBuilder
from taxed.models import (
    Challenge,
    Comparable,
    Property,
)
from taxed.state import conf


ADDR = 'https://api.gateway.attomdata.com/property/v2/salescomparables/address'
# ADDR = 'https://api.gateway.attomdata.com/property/v1.0.0/salescomparables/address'
HEADERS = {
    'apikey': conf.attom_key,
    'Accept': 'application/json',
}

PARAMS = {
    'searchType': 'Radius',
    'sameCity': True,
    'maxComps': 20,
    'miles': 5,
    'bedroomsRange': 2,
    'bathroomRange': 2,
    'sqFeetRange': 100,
    'lotSizeRange': 15000,
    'saleDateRange': 32,
    'yearBuiltRange': 40,
    'ownerOccupied': 'Both',
    'distressed': 'IncludeDistressed',
    'saleAmountRangeFrom': 50000,
}


def make_query_url(prop: Property) -> str:
    street = prop.street_1.replace('|', '').replace('/', '').\
        replace('-', '').replace(' ', '%20')
    city = prop.city.replace(' ', '%20')
    county = prop.county.replace(' ', '%20')
    state = prop.state.replace(' ', '%20')
    postal = prop.postal.replace(' ', '%20')

    query_url = f'{ADDR}/{street}/{city}/{county}/{state}/{postal}'
    return query_url


class AttomRequest:
    def __init__(self, prop: Property, params: dict):
        self.attom_status_code = -1
        self.body = {}
        self.prop = prop
        self.errors = []
        self.properties = []
        self.resp = requests.Response()
        self.status_code = -1
        self.params = params

    def did_attom_error(self, body: dict):
        code: str = ''
        msg: str = ''
        if 'Response' in body:
            response = body['Response']
            if 'status' in response:
                status = response['status']
                if 'code' in status:
                    code = status['code']
                    msg = status['msg']

        if code:
            self.errors.append(
                RuntimeError(f'Invalid status code from Attom: {code}\n{msg}'))

    def do_request(self):
        url = make_query_url(self.prop)
        plog.i(url)

        try:
            self.resp = requests.get(url,
                                     headers=HEADERS,
                                     params=self.params)

        except Exception as err:
            #TODO narrow this down from all exceptions
            #TODO email us
            msg = f'Request to Attom API failed:\n{err}'
            plog.wtf(msg)
            self.errors.append(msg)

        try:
            self.body = self.resp.json()
            self.did_attom_error(self.body)

            if len(self.errors) == 0:
                self.properties = self.body['RESPONSE_GROUP']['RESPONSE']\
                    ['RESPONSE_DATA']['PROPERTY_INFORMATION_RESPONSE_ext']\
                    ['SUBJECT_PROPERTY_ext']['PROPERTY']
                try:
                    self.attom_status_code = int(self.body['RESPONSE_GROUP']\
                        ['PRODUCT']['STATUS']['_Code'])
                except KeyError as err:
                    #TODO: this is a terribly hacked solution to Attom not returning
                    # a value  here on a successful api call
                    if '_Code' in str(err):
                        self.attom_status_code = 0
                plog.d(self.body)
        except Exception as err:
            #TODO narrow this down from all exceptions
            msg = (f'Parsing response from Attom API failed:\n'
                   f'{traceback.format_exc()}'
                   )
            self.errors.append(msg)
            plog.wtf(msg)
            # raise(err)


        if self.resp.status_code != 200:
            msg = (f'Bad HTTP status code from Attom: {self.resp.status_code}\n'
                   f'JSON: {self.body}')
            self.errors.append(msg)
            plog.wtf(msg)

        if self.attom_status_code != 0:
            msg = (f'Bad API status code from Attom: {self.attom_status_code}\n'
                   f'JSON: {self.body}')
            self.errors.append(msg)
            plog.wtf(msg)

        if len(self.properties) <= 1:
            msg = (f'No comparables found for property: '
                   f'{self.prop.property_id}, '
                   f'JSON: {self.body}')
            self.errors.append(msg)
            plog.wtf(msg)


class ComparablesCollector:
    def __init__(self,
                 challenge: Challenge,
                 target_prop: Property,
                 db: Session,
                 rb: ResponseBuilder):
        self.challenge = challenge
        self.target_prop = target_prop
        self.db = db
        self.properties_response = {}
        self.errors = []

        self.comparables = []
        self.cheap_comparables_to_use = []
        self.expensive_comparables_to_use = []

        self.rb = rb
        self.target_comp = Comparable()
        self.target_price = 0

    def run_all_steps(self):
        plog.i('getting attom data')
        self.get_attom_data()
        plog.i('reading comparables')
        self.read_comparables()
        plog.i('get more comparables')
        self.get_more_comparables_if_needed()
        plog.i('selecting_compables')
        self.select_and_prep_comparables_to_use()
        plog.i('save_compables')
        self.save_comparables_to_use()

    def get_attom_data(self):
        loops = 1
        for count in range(0, loops):
            plog.i(f'loop_count: {count}')
            self.errors = []

            ar = AttomRequest(self.target_prop, PARAMS)
            ar.do_request()
            self.properties_response = ar.properties

            self.errors.extend(ar.errors)

            if len(self.errors) == 0:
                # if no errors, break the loop and continue using the good data
                break
            else:
                plog.e(self.errors)

    def dedupe_comparables(self):
        addresses_seen = set()
        deduped_comps = []
        for comp in self.comparables:
            if comp.street_1 not in addresses_seen:
                deduped_comps.append(comp)
            addresses_seen.add(comp.street_1)
        self.comparables = deduped_comps

    def total_comparables_to_use_found(self) -> int:
        return len(self.comparables_to_use_combined())

    def comparables_to_use_combined(self) -> List[Comparable]:
        return self.cheap_comparables_to_use + self.expensive_comparables_to_use

    def all_comparables(self) -> List[Comparable]:
        return [self.target_comp] + self.comparables_to_use_combined()

    def read_comparables(self):
        for raw in self.properties_response:
            comp = Comparable()
            comp.comparable_id = uuid.uuid4()
            comp.challenge_id = self.challenge.challenge_id
            comp.target_property_id = self.target_prop.property_id
            comp.query_address = make_query_url(self.target_prop)
            comp.query_source = 'attom'

            if 'COMPARABLE_PROPERTY_ext' in raw:
                plog.i('comparable ------------------------------------------')
                data = raw['COMPARABLE_PROPERTY_ext']
                comp.miles = data['@DistanceFromSubjectPropertyMilesCount']
                comp.latitude = data['@LatitudeNumber']
                comp.longitude = data['@LongitudeNumber']
                sale_date = data['SALES_HISTORY']['@TransferDate_ext']
            else:
                plog.i('target ++++++++++++++++++++++++++++++++++++++++++')
                comp.property_id = self.target_prop.property_id
                plog.i(comp.property_id)
                data = raw
                comp.miles = '0'
                comp.latitude = data['_IDENTIFICATION']['@LatitudeNumber']
                comp.longitude = data['_IDENTIFICATION']['@LongitudeNumber']
                sale_date = data['SALES_HISTORY']['@PropertySalesDate']

                self.target_price = data['SALES_HISTORY']['@PropertySalesAmount']
                self.target_comp = comp

            comp.sale_date = sale_date.split('T')[0]

            comp.sale_price = data['SALES_HISTORY']['@PropertySalesAmount']
            comp.sqft_living = data['STRUCTURE']['@GrossLivingAreaSquareFeetCount']
            comp.sqft_lot = data['SITE']['@LotSquareFeetCount']

            comp.street_1 = data['@_StreetAddress']
            comp.city = data['@_City']
            comp.state = data['@_State']
            comp.postal = data['@_PostalCode']
            comp.parcel_id = data['_IDENTIFICATION']['@RTPropertyID_ext']

            comp.year_built = data['STRUCTURE']['STRUCTURE_ANALYSIS']\
                ['@PropertyStructureBuiltYear']
            comp.bath_count = data['STRUCTURE']['@TotalBathroomCount']
            comp.bed_count = data['STRUCTURE']['@TotalBedroomCount']

            comp.mortgage_holder = data['_OWNER']['@_Name']
            comp.assessed_price_1 = data['_TAX']['@_AssessorMarketValue_ext']
            comp.assessed_price_2 = data['_TAX']['@_TotalAssessedValueAmount']

            # bronze trident:
            # address['sale_date'] = sale_date, "%Y-%m-%dT%H:%M:%S").date

            if comp.sqft_lot == '':
                comp.is_data_damaged = True
                comp.sqft_lot = '0'
            else:
                comp.is_data_damaged = False

            if comp.sqft_living == '':
                comp.is_data_damaged = True
                comp.sqft_living = '0'
            else:
                comp.is_data_damaged = False

            if self.target_comp != comp:
                self.comparables.append(comp)

        self.dedupe_comparables()

    def get_more_comparables_if_needed(self):
        plog.i('getting more comparables (if needed)')
        sale_date_string = self.target_comp.sale_date
        if sale_date_string == '':
            sale_date_dt = datetime.strptime('1111-11-11', "%Y-%m-%d")
        else:
            sale_date_dt = datetime.strptime(sale_date_string, "%Y-%m-%d")

        years_delta = datetime.now() - sale_date_dt
        new_sale = years_delta.days < 365 * 3

        if new_sale and len(self.cheap_comparables_to_use) < 4:
            plog.d('New sale, need more cheap comparables')
            params = PARAMS.copy()
            params['saleAmountRangeTo'] = self.target_price

            loops = 1
            # loop until we get usable data for read_comparables
            for count in range(0, loops):
                plog.d(count)
                self.errors = []

                ar = AttomRequest(self.target_prop, params)
                ar.do_request()
                self.properties_response = ar.properties

                self.errors.extend(ar.errors)

                plog.e(self.errors)
                if len(self.errors) == 0:
                    # if no errors, break the loop and continue using the good data
                    break

            self.read_comparables()

    def select_and_prep_comparables_to_use(self):
        for comp in self.comparables:
            #TODO: what damaged data should we avoid using?
            # if not comp.is_data_damaged:
            if comp.sale_price <= self.target_price:
                if len(self.cheap_comparables_to_use) < 3:
                    self.cheap_comparables_to_use.append(comp)
                elif len(self.expensive_comparables_to_use) < 3:
                    self.expensive_comparables_to_use.append(comp)

        self.cheap_comparables_to_use.sort(key=lambda x: float(x.miles))
        self.expensive_comparables_to_use.sort(key=lambda x: float(x.miles))

        if self.total_comparables_to_use_found() < 3:
            msg = (f'Not enough comparables found for Property: '
                   f'{self.target_prop.property_id}')
            plog.wtf(msg)
            self.errors.append(msg)

        labels = ['L', 'K', 'J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
        self.target_comp.marker_label = 'P'

        for comp in self.comparables_to_use_combined():
            comp.marker_label = labels.pop()

    def save_comparables_to_use(self):
        for comp in self.comparables_to_use_combined():
            self.db.add(comp)
            db_commit(self.db, self.rb)
