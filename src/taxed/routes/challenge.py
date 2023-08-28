from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import uuid

from taxed.core import (
    ApiSchema,
    db_commit,
    ChallengeIdIn,
    EmptySchema,
    get_db,
    Gibs,
    nowstamp,
    plog,
    Policies,
    policy_fails,
    Puid,
    ResponseBuilder,
    send_email_with_attachments,
    SurferIdIn,
)
from taxed.models import (
    Challenge,
    Comparable,
    Probius,
    Project,
    Property,
    Surfer,
)
from taxed.state import conf
from taxed.challenges.challenge_builder import ChallengeBuilder
from taxed.challenges.comparables_builder import ComparablesBuilder
from taxed.challenges.comparables_collector import ComparablesCollector
from taxed.challenges.pdf_converter import convert_to_pdf

router = APIRouter()


class ChallengeCreateIn(ApiSchema):
    PropertyId: Puid

@router.post('/challenge/create', response_model=EmptySchema)
async def challenge_create(request: Request,
                           jin: ChallengeCreateIn,
                           db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    prop: Property = db.query(Property).filter(
        Property.property_id == jin.PropertyId).first() #type:ignore
    if prop is None:
        return rb.missing_requirement_response('property')

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.surfer_id == prop.surfer_id).first() #type:ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    project: Project = db.query(Project).filter(
        Project.project_id == surfer.project_id).first() #type:ignore
    if project is None:
        return rb.missing_requirement_response('project')

    probius: Probius = db.query(Probius).filter(
        Probius.probius_id == project.probius_id).first() #type:ignore
    if probius is None:
        return rb.missing_requirement_response('probius')

    challenge: Challenge = Challenge()
    challenge.challenge_id = uuid.uuid4()
    challenge.surfer_id = surfer.surfer_id
    challenge.target_property_id = prop.property_id
    challenge.time_created = nowstamp()
    db.add(challenge)
    db_commit(db, rb)

    plog.i('Collecting comparables...')
    cc = ComparablesCollector(challenge, prop, db, rb)
    plog.i('initiated')
    cc.run_all_steps()
    plog.i('COMPARABLES COLLECTED! Challenge building...')

    comp_build = ComparablesBuilder(cc)
    plog.i('initiated')
    comp_build.run_all_steps()
    plog.i('COMPARABLES BUILT!')

    chal_build = ChallengeBuilder(cc, surfer)
    chal_build.run_all_steps()
    plog.i('CHALLENGE BUILT!')

    body = (f'New request from {surfer.full_name()}, {surfer.email}, '
            f'{surfer.phone}.\n')

    # if prop.paper_mailing:
        # body += ('This user requested that a paper copy of these documents '
                    # 'be mailed to their home via USPS First Class mail.\n\n'
                    # f'{surfer.full_name()}\n'
                    # f'{prop.street_1}\n'
                    # f'{prop.city}, {prop.state} {prop.postal}')
    # else:
        # body += 'This user did not request a mailed copy.'

    doc_name = cc.target_comp.challenge_doc_path()
    doc_dir_temp = doc_name.split('/')[:-1]
    doc_dir = '/'.join(doc_dir_temp)
    convert_to_pdf(doc_name, doc_dir)

    send_email_with_attachments(
        conf,
        conf.email_documents,
        conf.email_document_recipients,
        'New Challenge Request',
        body,
        [cc.target_comp.comparables_doc_path(),
         cc.target_comp.challenge_doc_path()])

    probius.tokens_bought -= 1
    db.add(probius)
    db_commit(db, rb)

    rb.set_field('success', True)
    rb.set_field('message', 'Request approved, result sent to email.')
    return rb.build_response()


class ChallengeSchema(ApiSchema):
    ChallengeId: Puid
    SurferId: Puid
    TargetPropertyId: Puid
    TimeCreated: int

@router.post('/challenge/get.byId', response_model=ChallengeSchema)
async def challenge_get_by_id(request: Request,
                                      jin: ChallengeIdIn,
                                      db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    challenge: Challenge = db.query(Challenge).filter(
        Challenge.challenge_id == jin.ChallengeId).first()  #type:ignore
    if challenge is None:
        return rb.missing_requirement_response('challenge')

    rb.set_fields_with_dict(challenge.as_dict())
    return rb.build_response()


class ChallengeCollection(ApiSchema):
    Collection: List[ChallengeSchema]
    IdList: List[str]

@router.post('/challenges/get.bySurferId', response_model=ChallengeCollection)
async def challenges_get_by_surfer_id(request: Request,
                                      jin: SurferIdIn,
                                      db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    challenges = db.query(Challenge).filter(
        Challenge.surfer_id == jin.SurferId).all()  #type:ignore

    collection = []
    id_list = []
    for challenge in challenges:
        collection.append(challenge.as_dict())
        id_list.append(str(challenge.challenge_id))

    rb.set_field('Collection', collection)
    rb.set_field('IdList', id_list)
    return rb.build_response()


class ChallengeIdsIn(ApiSchema):
    ChallengeIds: List[Puid]

@router.post('/challenges/get.byIds', response_model=ChallengeCollection)
async def challenges_get_by_ids(request: Request,
                                jin: ChallengeIdsIn,
                                db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    collection = []
    for id in jin.ChallengeIds:
        challenge: Challenge = db.query(Challenge).filter(
            Challenge.challenge_id == id).first()  #type:ignore

        if challenge is not None:
            collection.append(challenge.as_dict())

    rb.set_field('Collection', collection)
    return rb.build_response()


@router.get('/challenge_doc/download/{challenge_id}', response_class=FileResponse)
async def challenge_doc_download(comparable_id: str,
                                 request: Request,
                                 db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    challenge: Challenge = db.query(Challenge).filter(
        Challenge.challenge_id == comparable_id).first()  #type:ignore
    if policy_fails(rb, 
                    await Policies.is_user_admin_of_challenge(gibs, challenge),
                    inspection_count= 2):
        return rb.policy_failed_response()

    comparable: Comparable = db.query(Comparable).filter(
        Comparable.property_id == challenge.target_property_id).first()  #type:ignore
    if comparable is None:
        return rb.missing_requirement_response('comparable')

    return FileResponse(comparable.challenge_doc_path())


@router.get('/comparable_doc/download/{challenge_id}', response_class=FileResponse)
async def comparable_doc_download(challenge_id: str,
                                  request: Request,
                                  db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    challenge: Challenge = db.query(Challenge).filter(
        Challenge.challenge_id == challenge_id).first()  #type:ignore
    if policy_fails(rb, 
                    await Policies.is_user_admin_of_challenge(gibs, challenge),
                    inspection_count= 2):
        return rb.policy_failed_response()

    comparable: Comparable = db.query(Comparable).filter(
        Comparable.property_id == challenge.target_property_id).first()  #type:ignore
    if comparable is None:
        return rb.missing_requirement_response('comparable')

    return FileResponse(comparable.comparables_doc_path())
