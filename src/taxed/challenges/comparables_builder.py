import os
import requests
from typing import List

from docx.shared import Inches
from docxtpl import DocxTemplate, InlineImage

from taxed.core import ApiSchema, plog
from taxed.models import (
    Comparable,
)
from taxed.challenges.comparables_collector import ComparablesCollector
from taxed.state import conf

STREET_URL = 'https://maps.googleapis.com/maps/api/streetview'


class ComparableContext(ApiSchema):
    comparable_address: str
    comparable_address_short: str
    dist: str
    sqrft: str
    lot: str
    sale: str
    year: str
    price: str
    comp_picture: object
    # comp_map: InlineImage
    parcel_id: str
    bedrooms: str
    bathrooms: str
    comp_number: int
    marker_label: str


class DocumentContext(ApiSchema):
    full_address: str
    full_address_short: str
    your_map:object
    your_picture: object
    your_parcel_id: str
    dist: str
    your_sqrft: str
    your_lot: str
    your_sale: str
    your_year: str
    your_price: str
    your_bedrooms: str
    your_bathrooms: str
    comp_number: int
    marker_label: str
    comparables: List[ComparableContext]


def sqft_lot_to_acres(size: str) -> str:
    lot = '%.2f' % (float(size) / 43560.0)
    if lot == '0.00':
        return '?'
    else:
        return lot


def get_google_street_image(comp: Comparable) -> bool:
    success = False
    loc = (f'{comp.street_1}, {comp.city}, {comp.state}, {comp.postal}')
    params = {
        'key': conf.google_places_key,
        'size': '600x400',
        'location': loc,
        'pitch': 10,
        'fov': 120,
    }

    resp = requests.get(STREET_URL, params=params)

    plog.i(f'getting street image for {comp.comparable_id}')
    plog.i(f'{loc}')
    plog.i(f'{len(resp.content)}')

    success = save_comp_street_image(comp, resp.content)
    return success

def get_mapquest_street_image(comp: Comparable) -> bool:
    success = False
    url = 'https://open.mapquestapi.com/staticmap/v5/map'
    focal = f'{comp.latitude},{comp.longitude}'
    params = {
        'key': conf.map_quest_key,
        'size': '600,400',
        'location': focal,
        'format': 'jpeg',
        'margin': 50,
        'center': focal,
        'zoom': 19,
        'type': 'hyb'
    }
    resp = requests.get(url, params=params)

    success = save_comp_street_image(comp, resp.content)
    return success


def save_comp_street_image(comp: Comparable, content: bytes) -> bool:
    success = False
    # TBG: I'm not convinced we need to check content-length
    if len(content) >= 80:
        comp.map_image = content
        plog.i(comp.street_image_path())

        with open(comp.street_image_path(), 'wb') as fil:
            fil.write(content)
        success = True
    else:
        plog.e(f'No street image for {comp.comparable_id}')

    return success


def get_and_save_map_image(comps: List[Comparable]):
    markers: str = ''
    map_image_path: str = ''

    markers = ''
    for comp in comps:
        markers += (f'&markers=label:{comp.marker_label}|'
                    f'{comp.latitude},{comp.longitude}|')

        if comp.is_target():
            map_image_path = comp.map_image_path()

    url = f'https://maps.googleapis.com/maps/api/staticmap?{markers}'
    params = {
        'key': conf.google_staticmaps_key,
        'size': '900x600',
        'format': 'jpg',
    }

    resp = requests.get(url,
                        params=params,
                        headers={"Content-Type": "application/json"})

    plog.debug(f'{url}, {resp.headers}')

    # all images will have the same path since they share challenge_request_id
    with open(map_image_path, 'wb') as fil:
        fil.write(resp.content)

    for comp in comps:
        if comp.is_target():
            comp.map_image = resp.content


class ComparablesBuilder:
    def __init__(self, cc: ComparablesCollector):
        self.cc = cc
        self.target_prop = cc.target_prop
        self.target_comp = cc.target_comp

        self.comp_doc = DocxTemplate(os.path.join(
            conf.path_templates, 'Comparables.docx'))

        plog.i('init doc context')
        self.document_context: DocumentContext
        self.init_document_context()

    def run_all_steps(self):
        plog.i('getting street images')
        self.get_street_images()

        plog.i('saving map image')
        get_and_save_map_image(self.cc.all_comparables())

        plog.i('set more doc context values')
        self.set_remaining_document_context_values()

        plog.i('write Comparables')
        self.write_comparables()

    def get_street_images(self):
        for comp in self.cc.all_comparables():
            success = get_google_street_image(comp)

            if not success:
                success = get_mapquest_street_image(comp)

    def write_comparables(self):
        self.comp_doc.render(dict(self.document_context))
        self.comp_doc.save(self.target_comp.comparables_doc_path())

    def init_document_context(self):
        comp = self.target_comp
        plog.i('target')
        self.document_context = DocumentContext(
            full_address = (f'{comp.street_1}, {comp.city}, '
                            f'{comp.state}, {comp.postal}'),
            full_address_short = (f'{comp.street_1} {comp.city}'),
            your_map = b'',
            your_picture = b'',
            your_parcel_id = comp.parcel_id,
            dist = 'N/A',
            your_sqrft = comp.sqft_living,
            your_lot = sqft_lot_to_acres(comp.sqft_lot),
            your_sale = comp.sale_date,
            your_year = comp.year_built,
            your_price = comp.sale_price,
            your_bedrooms = comp.bed_count,
            your_bathrooms = comp.bath_count,
            comp_number = 0,
            marker_label = comp.marker_label,
            comparables = [],
        )

    def set_remaining_document_context_values(self):
        plog.i(self.target_comp.map_image_path())
        plog.i(self.target_comp.street_image_path())

        self.target_comp.your_map = InlineImage(self.comp_doc,
                                           self.target_comp.map_image_path(),
                                           width=Inches(6.5))

        self.target_comp.your_picture = InlineImage(self.comp_doc,
                                               self.target_comp.street_image_path(),
                                               width=Inches(6.5))

        self.document_context.your_map = self.target_comp.your_map
        self.document_context.your_picture = self.target_comp.your_picture

        for comp in self.cc.all_comparables():
            plog.i('------------------------------------')
            plog.i(comp.map_image_path())
            plog.i(comp.street_image_path())

            comp.your_picture = InlineImage(self.comp_doc,
                                       comp.street_image_path(),
                                       width=Inches(6.5))

            self.document_context.comp_number += 1

            # plog.i('3')
            plog.i('comparable')
            comp_context = ComparableContext(
                comparable_address = (f'{comp.street_1}, {comp.city}, '
                                      f'{comp.state}, {comp.postal}'),
                comparable_address_short = f'{comp.street_1} {comp.city}',
                dist = '%.2f' % float(comp.miles),
                sqrft = comp.sqft_living,
                lot = sqft_lot_to_acres(comp.sqft_lot),
                year = comp.year_built,
                sale = comp.sale_date,
                price = comp.sale_price,
                comp_picture = comp.your_picture,
                # comp_map = comp.your_map,
                parcel_id = comp.parcel_id,
                bathrooms = comp.bath_count,
                bedrooms = comp.bed_count,
                marker_label = comp.marker_label,
                comp_number = self.document_context.comp_number,
            )
            self.document_context.comparables.append(comp_context)
