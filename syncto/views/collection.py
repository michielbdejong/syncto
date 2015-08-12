from pyramid.security import NO_PERMISSION_REQUIRED

from cliquet import Service
from cliquet.errors import raise_invalid

from syncto.authentication import build_sync_client
from syncto.utils import base64_to_uuid4, uuid4_to_base64


collection = Service(name='collection',
                     description='Firefox Sync Collection service',
                     path=('/buckets/syncto/collections'
                           '/{collection_name}/records'),
                     cors_headers=('Next-Page', 'Total-Records',
                                   'Last-Modified', 'ETag'))


@collection.get(permission=NO_PERMISSION_REQUIRED)
def collection_get(request):
    collection_name = request.matchdict['collection_name']
    sync_client = build_sync_client(request)

    params = {}
    if '_since' in request.GET:
        params['newer'] = request.GET['_since']

    if '_limit' in request.GET:
        params['limit'] = request.GET['_limit']

    if '_token' in request.GET:
        params['offset'] = request.GET['_token']

    if '_sort' in request.GET:
        if request.GET['_sort'] in ('-last_modified', 'newest'):
            params['sort'] = 'newest'

        elif request.GET['_sort'] in ('-sortindex', 'index'):
            params['sort'] = 'index'

        else:
            raise_invalid(request,
                          location="querystring",
                          name="_sort",
                          description=("_sort should be one of ("
                                       "'-last_modified', 'newest', "
                                       "'-sortindex', 'index')"))

    if 'ids' in request.GET:
        try:
            params['ids'] = [uuid4_to_base64(record_id.strip())
                             for record_id in request.GET['ids'].split(',')
                             if record_id]
        except ValueError:
            raise_invalid(request,
                          location="querystring",
                          name="ids",
                          description=("Invalid id in ids list."))

    records = sync_client.get_records(collection_name, full=True, **params)

    for r in records:
        r['last_modified'] = int(r.pop('modified') * 1000)
        r['id'] = base64_to_uuid4(r.pop('id'))

    # Configure headers
    response_headers = sync_client.raw_resp.headers
    headers = request.response.headers

    last_modified = float(response_headers['X-Last-Modified'])
    headers['ETag'] = '"%s"' % int(last_modified * 1000)
    request.response.last_modified = last_modified

    if 'X-Weave-Next-Offset' in response_headers:
        headers['Next-Page'] = response_headers['X-Weave-Next-Offset']

    if 'X-Weave-Records':
        headers['Total-Records'] = response_headers['X-Weave-Records']

    return {'data': records}
