def _cc_users_by_location(domain, location_id, include_docs=True, wrap=True, user_class=None):
    from corehq.apps.users.models import CommCareUser
    user_class = user_class or CommCareUser
    view = user_class.view if wrap else user_class.get_db().view
    return view(
        'users_extra/users_by_location_id',
        startkey=[domain, location_id, user_class.__name__],
        endkey=[domain, location_id, user_class.__name__, {}],
        include_docs=include_docs,
        reduce=False,
    )


def get_users_by_location_id(domain, location_id):
    """
    Get all mobile_workers for a given location
    """
    return _cc_users_by_location(domain, location_id)


def get_user_docs_by_location(domain, location_id):
    return _cc_users_by_location(domain, location_id, wrap=False).all()


def get_user_ids_by_location(domain, location_id):
    return [user['id'] for user in
            _cc_users_by_location(domain, location_id, include_docs=False)]


def get_one_user_at_location(domain, location_id):
    return _cc_users_by_location(domain, location_id).first()


def get_all_users_by_location(domain, location_id):
    from corehq.apps.users.models import CouchUser
    results = CouchUser.get_db().view(
        'users_extra/users_by_location_id',
        startkey=[domain, location_id],
        endkey=[domain, location_id, {}],
        include_docs=True,
        reduce=False,
    )
    return (CouchUser.wrap_correctly(res['doc']) for res in results)


def get_web_users_by_location(domain, location_id):
    from corehq.apps.users.models import WebUser
    return _cc_users_by_location(domain, location_id, user_class=WebUser)
