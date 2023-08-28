from datetime import date
import os
from typing import List

from docxtpl import DocxTemplate

from taxed.core import ApiSchema, plog
from taxed.models import (
    Challenge,
    Comparable,
    Property,
    Surfer,
)
from taxed.challenges.comparables_collector import ComparablesCollector
from taxed.state import conf


class ChallengeContext(ApiSchema):
    caps_official_city: str
    official_city: str
    unofficial_city: str
    challenge_period: int

    your_county: str
    full_name: str
    full_address: str
    full_address_short: str
    mailing_address: str
    us_phone: str
    your_email: str
    your_street: str
    your_price: str
    purchase_date: str
    your_claim: str
    yrla: str
    your_assess: str

    yrs: str
    fms: str
    vls: str
    css: str
    iss: str
    ots: str

    prp: str
    rs: str
    ra: str
    rd: str

    cshys: str = ''
    contys: str =  '✔'

    hr: str
    nhr: str
    hearys: str
    hearno: str

    # Not actually used
    imprvment_start: str
    imprvment_end: str
    description: str
    bld: str
    improvements: List[object]
    # comparables: List[Comparable]

    #TODO: (from bronze trident)
    # school_district
    # taxnum
    # docs


# class AddressContext(ApiSchema):
    # id: Puid


# class ImprovementContext(ApiSchema):
    # id: Puid


class ChallengeBuilder:
    def __init__(self, cc: ComparablesCollector, surfer: Surfer):
        self.comparables = cc
        self.challenge: Challenge = cc.challenge
        self.target_comp: Comparable = cc.target_comp
        self.target_prop: Property = cc.target_prop
        self.surfer = surfer

        self.challenge_doc = DocxTemplate(os.path.join(
            conf.path_templates, 'Challenge.docx'))

        self.context: ChallengeContext

    def run_all_steps(self):
        plog.i('create context')
        self.create_context()

        plog.i('write document')
        self.write_challenge()

    def create_context(self):
        # imps: Improvement = self.db.query(Improvement).filter( #type:ignore
            # Improvement.challenge_id == challenge.challenge_id).all()

        #TODO: implement improvements
        improvements = []
        # for imp in imps:
            # improvements.append(imp.as_dict())

        # if len(imps) == 0:
            # improvement_cost = ''
            # improvement_start = ''
            # improvement_end = ''
            # improvement_description = ''
        # else:
            # for imp in imps:
                # improvement_cost = ''
                # improvement_start = ''
                # improvement_end = ''
                # improvement_description = ''

        self.context = ChallengeContext(
            caps_official_city = self.target_comp.city.upper(),
            official_city = self.target_comp.city.lower().title(),
            unofficial_city = self.target_comp.city.lower().title(),
            challenge_period = date.today().year,

            full_address = self.target_comp.full_address(),
            full_address_short = self.target_comp.full_address_short(),
            your_county = self.target_prop.county.lower().title(),

            mailing_address = self.target_prop.address,
            full_name = self.surfer.full_name(),
            us_phone = self.surfer.phone,
            your_email = self.surfer.email,
            your_street = self.target_comp.street_1.lower().title(),
            your_price = self.target_comp.sale_price,
            your_claim = self.target_comp.assessed_price_1,
            yrla = self.target_comp.assessed_price_1,
            your_assess = self.target_comp.assessed_price_2,
            purchase_date = self.target_comp.sale_date,

            yrs = '✔' if self.target_prop.category == 'residential' else '',
            fms = '✔' if self.target_prop.category == 'farm' else '',
            vls = '✔' if self.target_prop.category == 'vacant' else '',
            css = '✔' if self.target_prop.category == 'commercial' else '',
            iss = '✔' if self.target_prop.category == 'industrial' else '',
            ots = '✔' if self.target_prop.category == 'other' else '',

            # these checkmarks go directly into the document
            prp = '✔' if self.challenge.reason_purchase_price else '',
            rd = '✔' if self.challenge.reason_description else '',
            ra = '✔' if self.challenge.reason_appraised else '',
            rs = '✔' if self.challenge.reason_recent_offer else '',

            hr = '\u2717' if self.challenge.hearing is True else '',
            nhr = '\u2717' if self.challenge.hearing is False else '',
            hearys = '✔' if self.challenge.hearing is True else '',
            hearno = '✔' if self.challenge.hearing is False else '',

            imprvment_start = '20',
            imprvment_end = '20',
            description = '20',
            bld = '✔' if len(improvements) else '',
            improvements = improvements,
        )

    def write_challenge(self):
        self.challenge_doc.render(dict(self.context))
        self.challenge_doc.save(self.target_comp.challenge_doc_path())
