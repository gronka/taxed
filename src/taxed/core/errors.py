from .generics import ApiError


DatabaseError = ApiError(
    code='database_error',
    msg='Error writing to database.')

LoginToChangeEmailError = ApiError(
    code='login_to_change_email',
    msg='You must be logged in to change your email.')

TokenExpiredError = ApiError(
    code='token_expired',
    msg='Token expired.')

TokenConsumedError = ApiError(
    code='token_consumed',
    msg='Token already applied.')

##
# Invalid role error
##
InvalidRoleError = ApiError(
    code='invalid_role',
    msg='Invalid role.')

##
# account errors
##

EmailRegisteredError = ApiError(
    code='email_registered',
    msg='Email is already registered.')

LoginFailedError = ApiError(
    code='login_failed',
    msg='Login failed.')

AccountNotFoundError = ApiError(
    code='account_not_found',
    msg='Account not found.')

EmailNotVerifiedError = ApiError(
    code='email_not_verified',
    msg=('This e-mail address is not verified. Please check your e-mail and '
         'click the link to verify'))

FailedToValidateWithGoogleError = ApiError(
    code='google_validation_failed',
    msg='Failed to validate your account with Google.')

FailedToValidateWithAppleError = ApiError(
    code='apple_validation_failed',
    msg='Failed to validate your account with Apple.')

