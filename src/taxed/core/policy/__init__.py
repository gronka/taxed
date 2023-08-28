from sqlalchemy.orm import Session
from typing import List

from taxed.core import (
    Gibs, 
    Puid,
    TWOS_UUID_STR,
    NINES_UUID_STR,
)
from taxed.core.auth import create_surfer_jwt_short
from taxed.core.response_builder import ResponseBuilder
from taxed.models import Challenge, Probius, Project


ADMINS = [TWOS_UUID_STR, NINES_UUID_STR]


class PolicyResult:
    '''Records whether a policy allowed user access or revoked it.

    (A long term goal of this class might be to roll up and unroll the results
    of all applied policies, but we don't have a need for that yet.)
    '''
    def __init__(self, allowed: bool):
        self.allowed: bool = allowed


class PolicyChain:
    '''The PolicyChain class houses static methods that return PolicyResult
    objects. We are able to apply complex Policy inquiries by applying
    combinations of PoliyChain methods and examining the returned PolicyResult.
    '''
    @classmethod
    def at_least_one_policy_must_allow(
        cls,
        policy_results: List[PolicyResult],
    ) -> PolicyResult:
        for policy_result in policy_results:
            if policy_result.allowed:
                return PolicyResult(allowed=True)
        return PolicyResult(allowed=False)

    @classmethod
    def all_policies_must_allow(
        cls,
        policy_results: List[PolicyResult],
    ) -> PolicyResult:
        for policy_result in policy_results:
            if not policy_result.allowed:
                return PolicyResult(allowed=False)
        return PolicyResult(allowed=True)


class Policies:
    '''The Policies class houses static methods that return PolicyResult
    objects.
    '''
    @classmethod
    async def public(cls) -> PolicyResult:
        return PolicyResult(allowed=True)

    @classmethod
    async def no_one(cls) -> PolicyResult:
        return PolicyResult(allowed=False)

    @classmethod
    async def is_user_super_admin(cls, gibs: Gibs) -> PolicyResult:
        if gibs.surfer_id() in ADMINS:
            return PolicyResult(allowed=True)
        return PolicyResult(allowed=False)

    @classmethod
    async def is_user_signed_in(cls,
                                gibs: Gibs,
                                db: Session,
                                rb: ResponseBuilder,
                                ) -> PolicyResult:
        if (await Policies.is_user_super_admin(gibs)).allowed:
            return PolicyResult(allowed=True)

        print('============================================')
        print(f'checking policy signed in: {gibs.is_jwt_short_valid()}')
        if gibs.is_jwt_short_valid():
            print('jwt short IS valid')
            return PolicyResult(allowed=True)
        else:
            print('jwt short IS NOT valid')
            if gibs.is_jwt_long_valid(db):
                print('jwt long IS valid')
                jwt_short = create_surfer_jwt_short(gibs.surfer_id())
                rb.set_field('NewJwtShort', jwt_short)
                gibs.jwt_short = jwt_short
                return PolicyResult(allowed=True)

        rb.set_field('NewJwtShort', 'signout')
        return PolicyResult(allowed=False)

    @classmethod
    async def is_user_this_surfer(
            cls,
            gibs: Gibs,
            surfer_id: Puid) -> PolicyResult:
        if (await Policies.is_user_super_admin(gibs)).allowed:
            return PolicyResult(allowed=True)

        if gibs.surfer_id() == str(surfer_id):
            return PolicyResult(allowed=True)
        return PolicyResult(allowed=False)

    @classmethod
    async def is_user_admin_of_challenge(
            cls,
            gibs: Gibs,
            challenge: Challenge) -> PolicyResult:
        if (await Policies.is_user_super_admin(gibs)).allowed:
            return PolicyResult(allowed=True)

        if gibs.surfer_id() == str(challenge.surfer_id):
            return PolicyResult(allowed=True)
        return PolicyResult(allowed=False)

    @classmethod
    async def is_user_admin_of_probius(
            cls,
            gibs: Gibs,
            probius: Probius) -> PolicyResult:
        if (await Policies.is_user_super_admin(gibs)).allowed:
            return PolicyResult(allowed=True)

        if gibs.surfer_id() == str(probius.creator_id):
            return PolicyResult(allowed=True)
        return PolicyResult(allowed=False)

    @classmethod
    async def is_user_admin_of_project(
            cls,
            gibs: Gibs,
            project: Project) -> PolicyResult:
        if (await Policies.is_user_super_admin(gibs)).allowed:
            return PolicyResult(allowed=True)

        if gibs.surfer_id() == str(project.creator_id):
            return PolicyResult(allowed=True)
        return PolicyResult(allowed=False)


class PolicyRunner:
    pass
    ## example PolicyRunner method
    # @classmethod
    # async def anon_or_surfer_owns_network_sub_id(
            # cls,
            # gibs: Gibs,
            # network_sub_id: Puid,
            # db: Session,
            # rb) -> NetworkSub:

        # network_sub: NetworkSub = db.query(NetworkSub).filter( #type:ignore
            # NetworkSub.network_sub_id == network_sub_id).first()

        # if network_sub.is_linked_to_surfer:
            # rb.exit_if_policy_fails(
                # await Policies.surfer_owns_network_sub(gibs, network_sub))
        # else:
            # rb.exit_if_policy_fails(await Policies.public())

        # return network_sub


def policy_fails(rb: ResponseBuilder,
                 policy_result: PolicyResult,
                 inspection_count = 1) -> bool:
    rb.policy_inspections += 1
    if rb.policy_inspections != inspection_count:
        raise RuntimeError('Policy inspection count mismatch: '
                           f'{rb.policy_inspections}')
    return not policy_result.allowed
